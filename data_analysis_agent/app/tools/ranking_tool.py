# 排行榜工具
# 设计目标：高效查询TOP-N排行，支持商品/品类/品牌/用户多个维度
# - 使用LEFT JOIN避免数据丢失
# - 单次SQL获取排行，限制limit≤50

import time
import json
from typing import Optional

from langchain.tools import tool

from ..database import get_db_connection
from .time_utils import parse_time_range


@tool
def query_product_ranking(
    rank_by: str = "revenue",
    time_range_text: str = "最近30天",
    category: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    查询商品排行榜，支持按销量/收入/评论数排序。

    参数：
    - rank_by: 排序维度：revenue(销售额) | sales(销量) | comment_count(评论数)
    - time_range_text: 时间范围，默认"最近30天"
    - category: 可选，品类过滤（如"手机"/"平板"）
    - brand: 可选，品牌过滤（如"华为"/"苹果"）
    - limit: 返回前N名，默认10，最大50

    返回：JSON格式排行数据 + chart_data（前端柱状图）
    """
    start_time = time.time()
    print(f"[工具] query_product_ranking 开始, rank_by={rank_by}, time={time_range_text}")

    if rank_by not in ["revenue", "sales", "comment_count"]:
        return f"不支持的排序维度: {rank_by}"
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

        # 构造WHERE条件
        where_parts = ["o.is_delete = 0"]
        params = []
        if rank_by in ["revenue", "sales"]:
            where_parts.append("o.create_time >= %s")
            where_parts.append("o.create_time <= %s")
            params.extend([f"{start} 00:00:00", f"{end} 23:59:59"])
            # 收入只算已支付订单
            if rank_by == "revenue":
                where_parts.append("o.pay_status = '1'")

        if category:
            where_parts.append("g.main_category = %s")
            params.append(category)
        if brand:
            where_parts.append("g.main_brand = %s")
            params.append(brand)

        where_clause = " AND ".join(where_parts)

        if rank_by == "revenue":
            sql = f"""
                SELECT g.sku_id, g.name, g.main_brand, g.main_category,
                       SUM(og.goods_num * COALESCE(g.p_price, g.jd_price, g.mk_price, 0)) AS metric_value,
                       SUM(og.goods_num) AS sales_count
                FROM goods g
                INNER JOIN order_goods og ON g.sku_id = og.sku_id
                INNER JOIN `order` o ON og.trade_no = o.trade_no
                WHERE {where_clause}
                GROUP BY g.sku_id, g.name, g.main_brand, g.main_category
                ORDER BY metric_value DESC
                LIMIT %s
            """
        elif rank_by == "sales":
            sql = f"""
                SELECT g.sku_id, g.name, g.main_brand, g.main_category,
                       SUM(og.goods_num) AS metric_value,
                       SUM(og.goods_num * COALESCE(g.p_price, g.jd_price, g.mk_price, 0)) AS revenue
                FROM goods g
                INNER JOIN order_goods og ON g.sku_id = og.sku_id
                INNER JOIN `order` o ON og.trade_no = o.trade_no
                WHERE {where_clause}
                GROUP BY g.sku_id, g.name, g.main_brand, g.main_category
                ORDER BY metric_value DESC
                LIMIT %s
            """
        else:  # comment_count
            # 评论数不受时间范围限制（评论表也有create_time，但商家通常关心总评论数）
            # 这里仍然加时间范围，只统计时间范围内的评论
            sql = f"""
                SELECT g.sku_id, g.name, g.main_brand, g.main_category,
                       COUNT(c.id) AS metric_value,
                       AVG(c.score) AS avg_score
                FROM goods g
                LEFT JOIN comment c ON g.sku_id = c.sku_id
                    AND c.create_time >= %s AND c.create_time <= %s
                WHERE 1=1
                {f"AND g.main_category = %s" if category else ""}
                {f"AND g.main_brand = %s" if brand else ""}
                GROUP BY g.sku_id, g.name, g.main_brand, g.main_category
                HAVING metric_value > 0
                ORDER BY metric_value DESC
                LIMIT %s
            """
            # 重新构造params
            params = [f"{start} 00:00:00", f"{end} 23:59:59"]
            if category:
                params.append(category)
            if brand:
                params.append(brand)

        params.append(limit)
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        elapsed = time.time() - start_time
        print(f"[工具] query_product_ranking 完成, 耗时{elapsed:.3f}s, 返回{len(rows)}条")

        cursor.close()
        conn.close()

        if not rows:
            return json.dumps({
                "rank_by": rank_by,
                "time_range": time_range,
                "ranking": [],
                "count": 0,
                "message": "该时间范围内无数据",
                "elapsed_sec": round(elapsed, 3)
            }, ensure_ascii=False, default=str)

        # 格式化结果
        metric_name = {"revenue": "销售额(元)", "sales": "销量(件)", "comment_count": "评论数(条)"}[rank_by]
        ranking = []
        for i, r in enumerate(rows, 1):
            ranking.append({
                "rank": i,
                "sku_id": r["sku_id"],
                "name": r["name"],
                "brand": r["main_brand"],
                "category": r["main_category"],
                "metric_value": float(r["metric_value"]) if r["metric_value"] else 0,
                "metric_name": metric_name,
                "avg_score": float(r["avg_score"]) if "avg_score" in r and r["avg_score"] else None
            })

        return json.dumps({
            "rank_by": rank_by,
            "rank_by_name": metric_name,
            "time_range": time_range,
            "filters": {"category": category, "brand": brand},
            "ranking": ranking,
            "count": len(ranking),
            "elapsed_sec": round(elapsed, 3),
            "chart_data": {
                "type": "bar",
                "title": f"商品排行榜（按{metric_name}） - {time_range['label']}",
                "x_axis": [r["name"][:15] + ("..." if len(r["name"]) > 15 else "") for r in ranking[:10]],
                "series": [{"name": metric_name, "data": [r["metric_value"] for r in ranking[:10]]}],
                "unit": "元" if rank_by == "revenue" else ""
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
        return f"查询商品排行时出错: {str(e)}"


@tool
def query_category_brand_ranking(
    rank_by: str = "revenue",
    group_by: str = "category",
    time_range_text: str = "最近30天",
    limit: int = 10
) -> str:
    """
    查询品类或品牌排行榜。

    参数：
    - rank_by: 排序维度：revenue(销售额) | sales(销量)
    - group_by: 分组维度：category(品类) | brand(品牌)
    - time_range_text: 时间范围，默认最近30天
    - limit: 返回前N名，默认10

    返回：JSON格式排行数据 + chart_data（饼图）
    """
    start_time = time.time()
    print(f"[工具] query_category_brand_ranking 开始, rank_by={rank_by}, group_by={group_by}")

    if rank_by not in ["revenue", "sales"]:
        return f"不支持的排序维度: {rank_by}"
    if group_by not in ["category", "brand"]:
        return f"不支持的分组维度: {group_by}"
    limit = max(1, min(limit, 50))

    time_range = parse_time_range(time_range_text)
    start = time_range["start_date"]
    end = time_range["end_date"]

    group_field = "g.main_category" if group_by == "category" else "g.main_brand"
    group_name = "品类" if group_by == "category" else "品牌"

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return "数据库连接失败"
        cursor = conn.cursor()

        metric_expr = "SUM(og.goods_num * COALESCE(g.p_price, g.jd_price, g.mk_price, 0))" if rank_by == "revenue" else "SUM(og.goods_num)"

        sql = f"""
            SELECT {group_field} AS group_name,
                   {metric_expr} AS metric_value,
                   COUNT(DISTINCT g.sku_id) AS product_count,
                   SUM(og.goods_num) AS sales_count
            FROM goods g
            INNER JOIN order_goods og ON g.sku_id = og.sku_id
            INNER JOIN `order` o ON og.trade_no = o.trade_no
            WHERE o.is_delete = 0
              AND o.create_time >= %s AND o.create_time <= %s
              {f"AND o.pay_status = '1'" if rank_by == "revenue" else ""}
              AND {group_field} IS NOT NULL AND {group_field} != ''
            GROUP BY {group_field}
            ORDER BY metric_value DESC
            LIMIT %s
        """
        cursor.execute(sql, (f"{start} 00:00:00", f"{end} 23:59:59", limit))
        rows = cursor.fetchall()

        elapsed = time.time() - start_time
        print(f"[工具] query_category_brand_ranking 完成, 耗时{elapsed:.3f}s, 返回{len(rows)}条")

        cursor.close()
        conn.close()

        if not rows:
            return json.dumps({
                "group_by": group_by,
                "rank_by": rank_by,
                "time_range": time_range,
                "ranking": [],
                "count": 0,
                "message": "无数据",
                "elapsed_sec": round(elapsed, 3)
            }, ensure_ascii=False, default=str)

        metric_name = "销售额(元)" if rank_by == "revenue" else "销量(件)"
        ranking = []
        for i, r in enumerate(rows, 1):
            ranking.append({
                "rank": i,
                "name": r["group_name"],
                "metric_value": float(r["metric_value"]) if r["metric_value"] else 0,
                "metric_name": metric_name,
                "product_count": int(r["product_count"]) if r["product_count"] else 0,
                "sales_count": int(r["sales_count"]) if r["sales_count"] else 0
            })

        return json.dumps({
            "group_by": group_by,
            "group_name": group_name,
            "rank_by": rank_by,
            "rank_by_name": metric_name,
            "time_range": time_range,
            "ranking": ranking,
            "count": len(ranking),
            "elapsed_sec": round(elapsed, 3),
            "chart_data": {
                "type": "pie",
                "title": f"{group_name}排行榜（按{metric_name}） - {time_range['label']}",
                "data": [{"name": r["name"], "value": r["metric_value"]} for r in ranking]
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
        return f"查询{group_name}排行时出错: {str(e)}"
