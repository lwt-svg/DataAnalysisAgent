# 评论分析工具
# 设计目标：商品评论/评分分析
# - 单次SQL获取评分分布 + 平均分 + 评论总数
# - 支持指定商品或全店范围

import time
import json
from typing import Optional

from langchain.tools import tool

from ..database import get_db_connection
from .time_utils import parse_time_range


@tool
def analyze_product_comments(
    sku_id: Optional[str] = None,
    product_name: Optional[str] = None,
    time_range_text: str = "最近30天"
) -> str:
    """
    商品评论分析：评分分布、平均分、评论量趋势。

    参数：
    - sku_id: 可选，指定商品SKU。留空表示全店分析
    - product_name: 可选，指定商品名称（模糊匹配）
    - time_range_text: 时间范围，默认最近30天

    返回：JSON格式评论分析 + chart_data（评分分布饼图 + 评论趋势折线）
    """
    start_time = time.time()
    print(f"[工具] analyze_product_comments 开始, sku={sku_id}, name={product_name}")

    time_range = parse_time_range(time_range_text)
    start = time_range["start_date"]
    end = time_range["end_date"]

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return "数据库连接失败"
        cursor = conn.cursor()

        # 构造WHERE条件
        where_parts = ["c.create_time >= %s", "c.create_time <= %s"]
        params = [f"{start} 00:00:00", f"{end} 23:59:59"]

        if sku_id:
            where_parts.append("c.sku_id = %s")
            params.append(sku_id)
        elif product_name:
            where_parts.append("g.name LIKE %s")
            params.append(f"%{product_name}%")

        where_clause = " AND ".join(where_parts)

        # 1. 评分分布 + 平均分 + 总评论数（单次SQL）
        sql_dist = f"""
            SELECT
                COUNT(*) AS total_count,
                AVG(c.score) AS avg_score,
                SUM(CASE WHEN c.score >= 4 THEN 1 ELSE 0 END) AS positive_count,
                SUM(CASE WHEN c.score = 3 THEN 1 ELSE 0 END) AS neutral_count,
                SUM(CASE WHEN c.score <= 2 THEN 1 ELSE 0 END) AS negative_count,
                SUM(CASE WHEN c.score = 5 THEN 1 ELSE 0 END) AS five_star,
                SUM(CASE WHEN c.score = 4 THEN 1 ELSE 0 END) AS four_star,
                SUM(CASE WHEN c.score = 3 THEN 1 ELSE 0 END) AS three_star,
                SUM(CASE WHEN c.score = 2 THEN 1 ELSE 0 END) AS two_star,
                SUM(CASE WHEN c.score = 1 THEN 1 ELSE 0 END) AS one_star
            FROM comment c
            {f"LEFT JOIN goods g ON c.sku_id = g.sku_id" if product_name else ""}
            WHERE {where_clause}
        """
        cursor.execute(sql_dist, params)
        dist = cursor.fetchone()

        # 2. 评论量按日趋势
        sql_trend = f"""
            SELECT DATE(c.create_time) AS dt, COUNT(*) AS cnt, AVG(c.score) AS avg_score
            FROM comment c
            {f"LEFT JOIN goods g ON c.sku_id = g.sku_id" if product_name else ""}
            WHERE {where_clause}
            GROUP BY DATE(c.create_time)
            ORDER BY dt
        """
        cursor.execute(sql_trend, params)
        trend_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        elapsed = time.time() - start_time
        print(f"[工具] analyze_product_comments 完成, 耗时{elapsed:.3f}s, 评论数{dist['total_count'] if dist else 0}")

        if not dist or dist["total_count"] == 0:
            return json.dumps({
                "sku_id": sku_id,
                "product_name": product_name,
                "time_range": time_range,
                "total_count": 0,
                "message": "该范围内无评论数据",
                "elapsed_sec": round(elapsed, 3)
            }, ensure_ascii=False, default=str)

        total = int(dist["total_count"])
        avg_score = float(dist["avg_score"]) if dist["avg_score"] else 0

        result = {
            "sku_id": sku_id,
            "product_name": product_name,
            "time_range": time_range,
            "total_count": total,
            "avg_score": round(avg_score, 2),
            "positive_rate": round(int(dist["positive_count"]) / total * 100, 1) if dist["positive_count"] else 0,
            "neutral_count": int(dist["neutral_count"]) if dist["neutral_count"] else 0,
            "negative_count": int(dist["negative_count"]) if dist["negative_count"] else 0,
            "negative_rate": round(int(dist["negative_count"]) / total * 100, 1) if dist["negative_count"] else 0,
            "score_distribution": {
                "5star": int(dist["five_star"]) if dist["five_star"] else 0,
                "4star": int(dist["four_star"]) if dist["four_star"] else 0,
                "3star": int(dist["three_star"]) if dist["three_star"] else 0,
                "2star": int(dist["two_star"]) if dist["two_star"] else 0,
                "1star": int(dist["one_star"]) if dist["one_star"] else 0
            },
            "trend": [
                {"date": str(r["dt"]), "count": int(r["cnt"]), "avg_score": float(r["avg_score"]) if r["avg_score"] else 0}
                for r in trend_rows
            ],
            "elapsed_sec": round(elapsed, 3),
            "chart_data": {
                "type": "composite",
                "title": f"评论分析 - {time_range['label']}",
                "charts": [
                    {
                        "type": "pie",
                        "title": "评分分布",
                        "data": [
                            {"name": "5星", "value": int(dist["five_star"]) if dist["five_star"] else 0},
                            {"name": "4星", "value": int(dist["four_star"]) if dist["four_star"] else 0},
                            {"name": "3星", "value": int(dist["three_star"]) if dist["three_star"] else 0},
                            {"name": "2星", "value": int(dist["two_star"]) if dist["two_star"] else 0},
                            {"name": "1星", "value": int(dist["one_star"]) if dist["one_star"] else 0}
                        ]
                    },
                    {
                        "type": "line",
                        "title": "评论量趋势",
                        "x_axis": [str(r["dt"]) for r in trend_rows],
                        "series": [{"name": "评论数", "data": [int(r["cnt"]) for r in trend_rows]}]
                    }
                ]
            }
        }

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        import traceback
        traceback.print_exc()
        if conn:
            try:
                conn.close()
            except:
                pass
        return f"评论分析时出错: {str(e)}"


@tool
def find_low_rated_products(
    time_range_text: str = "最近30天",
    limit: int = 10
) -> str:
    """
    查找差评最多的商品，帮助商家发现问题商品。

    参数：
    - time_range_text: 时间范围，默认最近30天
    - limit: 返回前N个商品，默认10

    返回：JSON格式差评商品列表 + chart_data
    """
    start_time = time.time()
    print(f"[工具] find_low_rated_products 开始, time={time_range_text}")

    limit = max(1, min(limit, 50))
    time_range = parse_time_range(time_range_text)
    start = time_range["start_date"]
    end = time_range["end_date"]

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return "数据库连接失败"
        cursor = conn.cursor()

        sql = """
            SELECT
                g.sku_id, g.name, g.main_brand, g.main_category,
                COUNT(c.id) AS total_comments,
                AVG(c.score) AS avg_score,
                SUM(CASE WHEN c.score <= 2 THEN 1 ELSE 0 END) AS negative_count,
                SUM(CASE WHEN c.score <= 2 THEN 1 ELSE 0 END) / COUNT(c.id) * 100 AS negative_rate
            FROM goods g
            INNER JOIN comment c ON g.sku_id = c.sku_id
            WHERE c.create_time >= %s AND c.create_time <= %s
            GROUP BY g.sku_id, g.name, g.main_brand, g.main_category
            HAVING negative_count > 0
            ORDER BY negative_count DESC, negative_rate DESC
            LIMIT %s
        """
        cursor.execute(sql, (f"{start} 00:00:00", f"{end} 23:59:59", limit))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        elapsed = time.time() - start_time
        print(f"[工具] find_low_rated_products 完成, 耗时{elapsed:.3f}s, 返回{len(rows)}条")

        if not rows:
            return json.dumps({
                "time_range": time_range,
                "products": [],
                "count": 0,
                "message": "该时间范围内无差评商品",
                "elapsed_sec": round(elapsed, 3)
            }, ensure_ascii=False, default=str)

        products = []
        for i, r in enumerate(rows, 1):
            products.append({
                "rank": i,
                "sku_id": r["sku_id"],
                "name": r["name"],
                "brand": r["main_brand"],
                "category": r["main_category"],
                "total_comments": int(r["total_comments"]),
                "avg_score": round(float(r["avg_score"]), 2) if r["avg_score"] else 0,
                "negative_count": int(r["negative_count"]),
                "negative_rate": round(float(r["negative_rate"]), 1) if r["negative_rate"] else 0
            })

        return json.dumps({
            "time_range": time_range,
            "products": products,
            "count": len(products),
            "elapsed_sec": round(elapsed, 3),
            "chart_data": {
                "type": "bar",
                "title": f"差评商品TOP{len(products)} - {time_range['label']}",
                "x_axis": [p["name"][:15] + ("..." if len(p["name"]) > 15 else "") for p in products],
                "series": [{"name": "差评数", "data": [p["negative_count"] for p in products]}]
            }
        }, ensure_ascii=False, default=str)

    except Exception as e:
        import traceback
        traceback.print_exc()
        if conn:
            try:
                conn.close()
            except:
                pass
        return f"查找差评商品时出错: {str(e)}"
