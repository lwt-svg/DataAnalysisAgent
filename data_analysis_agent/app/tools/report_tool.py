# 报告生成工具
# 设计目标：高效生成经营日报/周报
# - 使用ThreadPoolExecutor并行执行多个独立查询（DB查询是IO密集型）
# - 串行报告生成从5-8秒缩短至1-2秒（取决于最慢的查询）
# - 一次返回完整Markdown报告 + chart_data

import time
import json
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from langchain.tools import tool

from ..database import get_db_connection
from .time_utils import parse_time_range


def _query_single(conn_params: dict, sql: str, params: list) -> list:
    """在独立线程中执行单条SQL（线程安全的）"""
    from pymysql import connect
    from pymysql.cursors import DictCursor
    try:
        conn = connect(**conn_params, cursorclass=DictCursor)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[报告] 查询失败: {e}, SQL: {sql[:80]}")
        return []


def _parallel_queries(queries: list) -> list:
    """
    并行执行多个查询
    queries: [(name, sql, params), ...]
    返回: [(name, rows), ...] 顺序与输入一致
    """
    from ..config import DB_CONFIG
    # 构造pymysql连接参数
    conn_params = {
        "host": DB_CONFIG["host"],
        "user": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
        "database": DB_CONFIG["database"],
        "charset": "utf8mb4"
    }

    results = [None] * len(queries)
    with ThreadPoolExecutor(max_workers=min(6, len(queries))) as executor:
        # 提交所有任务
        future_to_idx = {}
        for i, (name, sql, params) in enumerate(queries):
            future = executor.submit(_query_single, conn_params, sql, params)
            future_to_idx[future] = i

        # 收集结果
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = (queries[idx][0], future.result())
            except Exception as e:
                results[idx] = (queries[idx][0], [])
                print(f"[报告] 查询异常: {e}")

    return results


def _format_money(v) -> str:
    """格式化金额：1.5万/1.2亿"""
    try:
        v = float(v)
    except:
        return "0"
    if v >= 100000000:
        return f"{v/100000000:.2f}亿"
    if v >= 10000:
        return f"{v/10000:.2f}万"
    return f"{v:.2f}"


def _format_pct(v) -> str:
    try:
        return f"{float(v):.1f}%"
    except:
        return "0%"


@tool
def generate_daily_report(date_text: Optional[str] = None) -> str:
    """
    生成经营日报（并行查询6个维度数据）。

    参数：
    - date_text: 可选，指定日期(YYYY-MM-DD)，默认今天

    返回：JSON格式，包含Markdown报告 + 关键指标 + chart_data
    """
    start_time = time.time()
    print(f"[工具] generate_daily_report 开始, date={date_text}")

    # 解析日期
    if date_text:
        try:
            target_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except:
            target_date = date.today()
    else:
        target_date = date.today()

    date_str = target_date.isoformat()
    date_start = f"{date_str} 00:00:00"
    date_end = f"{date_str} 23:59:59"

    # 昨天数据（用于环比）
    yesterday = target_date - timedelta(days=1)
    y_start = f"{yesterday.isoformat()} 00:00:00"
    y_end = f"{yesterday.isoformat()} 23:59:59"

    # 构造6个并行查询
    queries = [
        # 1. 今日GMV + 订单数 + 客单价
        ("today_summary", """
            SELECT
                COUNT(*) AS order_count,
                SUM(CASE WHEN pay_status = '1' THEN order_amount ELSE 0 END) AS gmv,
                AVG(CASE WHEN pay_status = '1' THEN order_amount ELSE NULL END) AS avg_order_amount,
                SUM(CASE WHEN pay_status = '1' THEN 1 ELSE 0 END) AS paid_count,
                SUM(CASE WHEN pay_status = '0' THEN 1 ELSE 0 END) AS unpaid_count
            FROM `order`
            WHERE is_delete = 0 AND create_time >= %s AND create_time <= %s
        """, [date_start, date_end]),
        # 2. 昨日GMV + 订单数（用于环比）
        ("yesterday_summary", """
            SELECT
                COUNT(*) AS order_count,
                SUM(CASE WHEN pay_status = '1' THEN order_amount ELSE 0 END) AS gmv
            FROM `order`
            WHERE is_delete = 0 AND create_time >= %s AND create_time <= %s
        """, [y_start, y_end]),
        # 3. 今日新增用户数
        ("today_new_users", """
            SELECT COUNT(*) AS cnt
            FROM user
            WHERE DATE(create_time) = %s
        """, [date_str]),
        # 4. 今日TOP5热销商品
        ("today_top5_products", """
            SELECT g.sku_id, g.name, g.main_brand,
                   SUM(og.goods_num) AS sales_count,
                   SUM(og.goods_num * COALESCE(g.p_price, g.jd_price, g.mk_price, 0)) AS revenue
            FROM goods g
            INNER JOIN order_goods og ON g.sku_id = og.sku_id
            INNER JOIN `order` o ON og.trade_no = o.trade_no
            WHERE o.is_delete = 0 AND o.pay_status = '1'
              AND o.create_time >= %s AND o.create_time <= %s
            GROUP BY g.sku_id, g.name, g.main_brand
            ORDER BY revenue DESC
            LIMIT 5
        """, [date_start, date_end]),
        # 5. 今日评论数 + 平均分
        ("today_comments", """
            SELECT COUNT(*) AS comment_count, AVG(score) AS avg_score
            FROM comment
            WHERE create_time >= %s AND create_time <= %s
        """, [date_start, date_end]),
        # 6. 今日品类销售分布
        ("today_category_distribution", """
            SELECT g.main_category AS category,
                   SUM(og.goods_num * COALESCE(g.p_price, g.jd_price, g.mk_price, 0)) AS revenue
            FROM goods g
            INNER JOIN order_goods og ON g.sku_id = og.sku_id
            INNER JOIN `order` o ON og.trade_no = o.trade_no
            WHERE o.is_delete = 0 AND o.pay_status = '1'
              AND o.create_time >= %s AND o.create_time <= %s
              AND g.main_category IS NOT NULL AND g.main_category != ''
            GROUP BY g.main_category
            ORDER BY revenue DESC
            LIMIT 10
        """, [date_start, date_end])
    ]

    # 并行执行
    results = _parallel_queries(queries)
    result_dict = {name: rows for name, rows in results}

    elapsed_query = time.time() - start_time
    print(f"[工具] 报告6个查询并行完成, 耗时{elapsed_query:.3f}s")

    # 解析数据
    today = result_dict.get("today_summary", [])
    yesterday = result_dict.get("yesterday_summary", [])
    new_users = result_dict.get("today_new_users", [])
    top5 = result_dict.get("today_top5_products", [])
    comments = result_dict.get("today_comments", [])
    category_dist = result_dict.get("today_category_distribution", [])

    today_data = today[0] if today else {}
    yesterday_data = yesterday[0] if yesterday else {}
    new_user_count = new_users[0]["cnt"] if new_users else 0
    comment_data = comments[0] if comments else {}

    gmv = float(today_data.get("gmv", 0) or 0)
    order_count = int(today_data.get("order_count", 0) or 0)
    avg_order = float(today_data.get("avg_order_amount", 0) or 0)
    paid_count = int(today_data.get("paid_count", 0) or 0)
    unpaid_count = int(today_data.get("unpaid_count", 0) or 0)

    y_gmv = float(yesterday_data.get("gmv", 0) or 0)
    y_order_count = int(yesterday_data.get("order_count", 0) or 0)

    gmv_change = ((gmv - y_gmv) / y_gmv * 100) if y_gmv > 0 else None
    order_change = ((order_count - y_order_count) / y_order_count * 100) if y_order_count > 0 else None

    comment_count = int(comment_data.get("comment_count", 0) or 0)
    avg_score = float(comment_data.get("avg_score", 0) or 0)

    # 构造Markdown报告
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][target_date.weekday()]
    md_lines = [
        f"# 📊 经营日报 - {date_str}（{weekday_cn}）",
        "",
        "## 一、核心指标",
        "",
        f"| 指标 | 今日 | 昨日 | 环比 |",
        f"|------|------|------|------|",
        f"| GMV(销售额) | ¥{_format_money(gmv)} | ¥{_format_money(y_gmv)} | {_format_pct(gmv_change) if gmv_change is not None else '-'} |",
        f"| 订单量 | {order_count} | {y_order_count} | {_format_pct(order_change) if order_change is not None else '-'} |",
        f"| 客单价 | ¥{avg_order:.2f} | - | - |",
        f"| 已支付订单 | {paid_count} | - | - |",
        f"| 待支付订单 | {unpaid_count} | - | - |",
        f"| 新增用户 | {new_user_count} | - | - |",
        f"| 新增评论 | {comment_count} | - | - |",
        f"| 平均评分 | {avg_score:.2f} | - | - |",
        ""
    ]

    # TOP5商品
    if top5:
        md_lines.extend([
            "## 二、今日热销TOP5",
            "",
            "| 排名 | 商品 | 品牌 | 销量 | 销售额 |",
            "|------|------|------|------|--------|"
        ])
        for i, p in enumerate(top5, 1):
            md_lines.append(
                f"| {i} | {p['name']} | {p['main_brand'] or '-'} | "
                f"{int(p['sales_count'])}件 | ¥{_format_money(p['revenue'])} |"
            )
        md_lines.append("")

    # 品类分布
    if category_dist:
        md_lines.extend([
            "## 三、品类销售分布",
            "",
            "| 品类 | 销售额 | 占比 |",
            "|------|--------|------|"
        ])
        total_cat = sum(float(c["revenue"]) for c in category_dist)
        for c in category_dist:
            pct = (float(c["revenue"]) / total_cat * 100) if total_cat > 0 else 0
            md_lines.append(
                f"| {c['category']} | ¥{_format_money(c['revenue'])} | {pct:.1f}% |"
            )
        md_lines.append("")

    md_lines.extend([
        "## 四、经营建议",
        ""
    ])

    # 简单的建议规则
    advices = []
    if gmv_change is not None and gmv_change < -10:
        advices.append(f"- ⚠️ GMV环比下降{abs(gmv_change):.1f}%，建议关注流量来源和转化率")
    if gmv_change is not None and gmv_change > 10:
        advices.append(f"- ✅ GMV环比增长{gmv_change:.1f}%，可分析增长原因复制到其他品类")
    if unpaid_count > paid_count and paid_count > 0:
        advices.append(f"- ⚠️ 待支付订单({unpaid_count})多于已支付({paid_count})，建议发送催付提醒")
    if avg_score > 0 and avg_score < 4:
        advices.append(f"- ⚠️ 平均评分{avg_score:.2f}偏低，建议排查差评商品")
    if not advices:
        advices.append("- 经营状况正常，建议持续关注趋势变化")

    md_lines.extend(advices)
    md_lines.append("")
    md_lines.append(f"\n---\n*报告生成耗时: {time.time() - start_time:.2f}s | 数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    markdown_report = "\n".join(md_lines)
    elapsed = time.time() - start_time
    print(f"[工具] generate_daily_report 完成, 总耗时{elapsed:.3f}s")

    return json.dumps({
        "report_type": "daily",
        "report_date": date_str,
        "markdown": markdown_report,
        "metrics": {
            "gmv": gmv,
            "order_count": order_count,
            "avg_order_amount": avg_order,
            "paid_count": paid_count,
            "unpaid_count": unpaid_count,
            "new_user_count": new_user_count,
            "comment_count": comment_count,
            "avg_score": avg_score,
            "gmv_change_pct": gmv_change,
            "order_change_pct": order_change
        },
        "top5_products": [
            {
                "name": p["name"],
                "brand": p["main_brand"],
                "sales_count": int(p["sales_count"]),
                "revenue": float(p["revenue"])
            } for p in top5
        ],
        "category_distribution": [
            {
                "category": c["category"],
                "revenue": float(c["revenue"])
            } for c in category_dist
        ],
        "elapsed_sec": round(elapsed, 3),
        "chart_data": {
            "type": "composite",
            "title": f"经营日报 - {date_str}",
            "charts": [
                {
                    "type": "bar",
                    "title": "今日热销TOP5",
                    "x_axis": [p["name"][:12] + ("..." if len(p["name"]) > 12 else "") for p in top5],
                    "series": [{"name": "销售额", "data": [float(p["revenue"]) for p in top5]}],
                    "unit": "元"
                },
                {
                    "type": "pie",
                    "title": "品类销售分布",
                    "data": [{"name": c["category"], "value": float(c["revenue"])} for c in category_dist]
                }
            ]
        }
    }, ensure_ascii=False, default=str)


@tool
def generate_weekly_report(week_offset: int = 0) -> str:
    """
    生成经营周报（最近7天）。

    参数：
    - week_offset: 周偏移量，0=本周, -1=上周

    返回：JSON格式，包含Markdown周报 + chart_data
    """
    start_time = time.time()
    print(f"[工具] generate_weekly_report 开始, week_offset={week_offset}")

    today = date.today()
    # 本周一
    monday = today - timedelta(days=today.weekday())
    # 应用偏移
    monday = monday + timedelta(days=week_offset * 7)
    sunday = monday + timedelta(days=6)

    start = monday.isoformat()
    end = sunday.isoformat()

    # 上周数据（用于环比）
    prev_monday = monday - timedelta(days=7)
    prev_sunday = sunday - timedelta(days=7)
    p_start = prev_monday.isoformat()
    p_end = prev_sunday.isoformat()

    # 构造并行查询
    queries = [
        # 1. 本周GMV/订单数/客单价
        ("this_week_summary", """
            SELECT
                COUNT(*) AS order_count,
                SUM(CASE WHEN pay_status = '1' THEN order_amount ELSE 0 END) AS gmv,
                AVG(CASE WHEN pay_status = '1' THEN order_amount ELSE NULL END) AS avg_order_amount,
                COUNT(DISTINCT email) AS active_users
            FROM `order`
            WHERE is_delete = 0 AND create_time >= %s AND create_time <= %s
        """, [f"{start} 00:00:00", f"{end} 23:59:59"]),
        # 2. 上周GMV/订单数
        ("last_week_summary", """
            SELECT
                COUNT(*) AS order_count,
                SUM(CASE WHEN pay_status = '1' THEN order_amount ELSE 0 END) AS gmv
            FROM `order`
            WHERE is_delete = 0 AND create_time >= %s AND create_time <= %s
        """, [f"{p_start} 00:00:00", f"{p_end} 23:59:59"]),
        # 3. 本周每日GMV趋势
        ("daily_gmv_trend", """
            SELECT
                DATE(create_time) AS dt,
                SUM(CASE WHEN pay_status = '1' THEN order_amount ELSE 0 END) AS gmv,
                COUNT(*) AS order_count
            FROM `order`
            WHERE is_delete = 0 AND create_time >= %s AND create_time <= %s
            GROUP BY DATE(create_time)
            ORDER BY dt
        """, [f"{start} 00:00:00", f"{end} 23:59:59"]),
        # 4. 本周TOP10商品
        ("top10_products", """
            SELECT g.sku_id, g.name, g.main_brand, g.main_category,
                   SUM(og.goods_num) AS sales_count,
                   SUM(og.goods_num * COALESCE(g.p_price, g.jd_price, g.mk_price, 0)) AS revenue
            FROM goods g
            INNER JOIN order_goods og ON g.sku_id = og.sku_id
            INNER JOIN `order` o ON og.trade_no = o.trade_no
            WHERE o.is_delete = 0 AND o.pay_status = '1'
              AND o.create_time >= %s AND o.create_time <= %s
            GROUP BY g.sku_id, g.name, g.main_brand, g.main_category
            ORDER BY revenue DESC
            LIMIT 10
        """, [f"{start} 00:00:00", f"{end} 23:59:59"]),
        # 5. 本周品类销售
        ("category_sales", """
            SELECT g.main_category AS category,
                   SUM(og.goods_num) AS sales_count,
                   SUM(og.goods_num * COALESCE(g.p_price, g.jd_price, g.mk_price, 0)) AS revenue
            FROM goods g
            INNER JOIN order_goods og ON g.sku_id = og.sku_id
            INNER JOIN `order` o ON og.trade_no = o.trade_no
            WHERE o.is_delete = 0 AND o.pay_status = '1'
              AND o.create_time >= %s AND o.create_time <= %s
              AND g.main_category IS NOT NULL AND g.main_category != ''
            GROUP BY g.main_category
            ORDER BY revenue DESC
        """, [f"{start} 00:00:00", f"{end} 23:59:59"]),
        # 6. 本周评论情况
        ("week_comments", """
            SELECT COUNT(*) AS comment_count, AVG(score) AS avg_score
            FROM comment
            WHERE create_time >= %s AND create_time <= %s
        """, [f"{start} 00:00:00", f"{end} 23:59:59"])
    ]

    results = _parallel_queries(queries)
    result_dict = {name: rows for name, rows in results}

    elapsed_query = time.time() - start_time
    print(f"[工具] 周报6个查询并行完成, 耗时{elapsed_query:.3f}s")

    this_week = result_dict.get("this_week_summary", [{}])
    last_week = result_dict.get("last_week_summary", [{}])
    daily_trend = result_dict.get("daily_gmv_trend", [])
    top10 = result_dict.get("top10_products", [])
    cat_sales = result_dict.get("category_sales", [])
    week_comments = result_dict.get("week_comments", [{}])

    tw = this_week[0] if this_week else {}
    lw = last_week[0] if last_week else {}
    wc = week_comments[0] if week_comments else {}

    gmv = float(tw.get("gmv", 0) or 0)
    order_count = int(tw.get("order_count", 0) or 0)
    avg_order = float(tw.get("avg_order_amount", 0) or 0)
    active_users = int(tw.get("active_users", 0) or 0)
    comment_count = int(wc.get("comment_count", 0) or 0)
    avg_score = float(wc.get("avg_score", 0) or 0)

    l_gmv = float(lw.get("gmv", 0) or 0)
    l_order_count = int(lw.get("order_count", 0) or 0)

    gmv_change = ((gmv - l_gmv) / l_gmv * 100) if l_gmv > 0 else None
    order_change = ((order_count - l_order_count) / l_order_count * 100) if l_order_count > 0 else None

    # 构造Markdown周报
    period_label = "本周" if week_offset == 0 else ("上周" if week_offset == -1 else f"第{week_offset}周")
    md_lines = [
        f"# 📈 经营周报 - {period_label}（{start} ~ {end}）",
        "",
        "## 一、本周核心指标",
        "",
        f"| 指标 | 本周 | 上周 | 环比 |",
        f"|------|------|------|------|",
        f"| GMV | ¥{_format_money(gmv)} | ¥{_format_money(l_gmv)} | {_format_pct(gmv_change) if gmv_change is not None else '-'} |",
        f"| 订单量 | {order_count} | {l_order_count} | {_format_pct(order_change) if order_change is not None else '-'} |",
        f"| 客单价 | ¥{avg_order:.2f} | - | - |",
        f"| 活跃用户 | {active_users} | - | - |",
        f"| 新增评论 | {comment_count} | - | - |",
        f"| 平均评分 | {avg_score:.2f} | - | - |",
        ""
    ]

    # 每日趋势
    if daily_trend:
        md_lines.extend([
            "## 二、每日GMV趋势",
            "",
            "| 日期 | GMV | 订单量 |",
            "|------|-----|--------|"
        ])
        for d in daily_trend:
            md_lines.append(
                f"| {d['dt']} | ¥{_format_money(d['gmv'])} | {int(d['order_count'])} |"
            )
        md_lines.append("")

    # TOP10商品
    if top10:
        md_lines.extend([
            "## 三、本周热销TOP10",
            "",
            "| 排名 | 商品 | 品牌 | 品类 | 销量 | 销售额 |",
            "|------|------|------|------|------|--------|"
        ])
        for i, p in enumerate(top10, 1):
            md_lines.append(
                f"| {i} | {p['name']} | {p['main_brand'] or '-'} | "
                f"{p['main_category'] or '-'} | {int(p['sales_count'])}件 | ¥{_format_money(p['revenue'])} |"
            )
        md_lines.append("")

    # 品类表现
    if cat_sales:
        md_lines.extend([
            "## 四、品类表现",
            "",
            "| 品类 | 销量 | 销售额 |",
            "|------|------|--------|"
        ])
        for c in cat_sales:
            md_lines.append(
                f"| {c['category']} | {int(c['sales_count'])}件 | ¥{_format_money(c['revenue'])} |"
            )
        md_lines.append("")

    # 下周建议
    md_lines.extend([
        "## 五、下周建议",
        ""
    ])
    advices = []
    if gmv_change is not None and gmv_change < 0:
        advices.append(f"- ⚠️ GMV环比下降{abs(gmv_change):.1f}%，需关注流量与转化")
    if gmv_change is not None and gmv_change > 0:
        advices.append(f"- ✅ GMV环比增长{gmv_change:.1f}%，分析成功因素复制推广")
    if avg_score > 0 and avg_score < 4:
        advices.append(f"- ⚠️ 平均评分{avg_score:.2f}偏低，重点关注差评商品")
    if order_count > 0 and active_users > 0 and (order_count - active_users) > 0:
        advices.append("- 建议优化催付流程，提升支付转化率")
    if not advices:
        advices.append("- 经营状况稳定，持续监控关键指标")

    md_lines.extend(advices)
    md_lines.append("")
    md_lines.append(f"\n---\n*报告生成耗时: {time.time() - start_time:.2f}s | 数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    markdown_report = "\n".join(md_lines)
    elapsed = time.time() - start_time
    print(f"[工具] generate_weekly_report 完成, 总耗时{elapsed:.3f}s")

    return json.dumps({
        "report_type": "weekly",
        "period": {"start": start, "end": end, "label": period_label},
        "markdown": markdown_report,
        "metrics": {
            "gmv": gmv,
            "order_count": order_count,
            "avg_order_amount": avg_order,
            "active_users": active_users,
            "comment_count": comment_count,
            "avg_score": avg_score,
            "gmv_change_pct": gmv_change,
            "order_change_pct": order_change
        },
        "daily_trend": [
            {"date": str(d["dt"]), "gmv": float(d["gmv"]), "order_count": int(d["order_count"])}
            for d in daily_trend
        ],
        "top10_products": [
            {
                "name": p["name"],
                "brand": p["main_brand"],
                "category": p["main_category"],
                "sales_count": int(p["sales_count"]),
                "revenue": float(p["revenue"])
            } for p in top10
        ],
        "elapsed_sec": round(elapsed, 3),
        "chart_data": {
            "type": "composite",
            "title": f"经营周报 - {period_label}",
            "charts": [
                {
                    "type": "line",
                    "title": "每日GMV趋势",
                    "x_axis": [str(d["dt"]) for d in daily_trend],
                    "series": [{"name": "GMV", "data": [float(d["gmv"]) for d in daily_trend]}],
                    "unit": "元"
                },
                {
                    "type": "bar",
                    "title": "热销TOP10",
                    "x_axis": [p["name"][:12] + ("..." if len(p["name"]) > 12 else "") for p in top10[:10]],
                    "series": [{"name": "销售额", "data": [float(p["revenue"]) for p in top10[:10]]}],
                    "unit": "元"
                }
            ]
        }
    }, ensure_ascii=False, default=str)
