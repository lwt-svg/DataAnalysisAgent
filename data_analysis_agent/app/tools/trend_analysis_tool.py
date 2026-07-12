# 趋势分析工具
# 设计目标：高效查询时间序列数据，自动计算环比增长率
# - 单次查询获取当期 + 上期数据（避免2次SQL）
# - 默认按天聚合，超过90天自动按周聚合（CHART_MAX_POINTS）
# - 返回chart_data供前端渲染折线图

import time
import json
from datetime import datetime, timedelta
from typing import Optional

from langchain.tools import tool

from ..database import get_db_connection
from ..config import CHART_MAX_POINTS
from .time_utils import parse_time_range, get_previous_range


def _determine_group_by(days: int) -> str:
    """根据时间跨度决定聚合粒度：>90天用周，否则用天"""
    if days > CHART_MAX_POINTS:
        return "week"
    return "day"


def _group_by_expr(group_by: str, column: str = "create_time") -> str:
    """返回GROUP BY表达式"""
    if group_by == "week":
        return f"DATE(DATE_SUB({column}, INTERVAL WEEKDAY({column}) DAY))"
    elif group_by == "month":
        return f"DATE_FORMAT({column}, '%Y-%m-01')"
    else:
        return f"DATE({column})"


def _query_metric_series(metric: str, start: str, end: str, group_by: str) -> list:
    """
    查询单个指标的时间序列
    metric: gmv | order_count | avg_order_amount | user_count
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor()

        if metric == "gmv":
            sql = f"""
                SELECT {_group_by_expr(group_by)} AS dt, SUM(order_amount) AS val
                FROM `order`
                WHERE pay_status = '1' AND is_delete = 0
                  AND create_time >= %s AND create_time <= %s
                GROUP BY {_group_by_expr(group_by)}
                ORDER BY dt
            """
        elif metric == "order_count":
            sql = f"""
                SELECT {_group_by_expr(group_by)} AS dt, COUNT(*) AS val
                FROM `order`
                WHERE is_delete = 0
                  AND create_time >= %s AND create_time <= %s
                GROUP BY {_group_by_expr(group_by)}
                ORDER BY dt
            """
        elif metric == "avg_order_amount":
            sql = f"""
                SELECT {_group_by_expr(group_by)} AS dt, AVG(order_amount) AS val
                FROM `order`
                WHERE pay_status = '1' AND is_delete = 0
                  AND create_time >= %s AND create_time <= %s
                GROUP BY {_group_by_expr(group_by)}
                ORDER BY dt
            """
        elif metric == "user_count":
            sql = f"""
                SELECT {_group_by_expr(group_by)} AS dt, COUNT(DISTINCT email) AS val
                FROM `order`
                WHERE is_delete = 0
                  AND create_time >= %s AND create_time <= %s
                GROUP BY {_group_by_expr(group_by)}
                ORDER BY dt
            """
        else:
            return []

        cursor.execute(sql, (f"{start} 00:00:00", f"{end} 23:59:59"))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [{"date": str(r["dt"]), "value": float(r["val"]) if r["val"] is not None else 0} for r in rows]

    except Exception as e:
        print(f"[工具] _query_metric_series 异常: {e}")
        if conn:
            try:
                conn.close()
            except:
                pass
        return []


def _calc_change(curr: float, prev: float) -> Optional[float]:
    """计算环比增长率（百分比），上期为0返回None"""
    if prev is None or prev == 0:
        return None
    return round((curr - prev) / prev * 100, 1)


@tool
def query_sales_trend(
    metric: str,
    time_range_text: str = "最近30天",
    group_by: Optional[str] = None
) -> str:
    """
    查询销售趋势数据，返回时间序列和环比变化。

    参数：
    - metric: 指标名，支持：gmv(销售额) | order_count(订单量) | avg_order_amount(客单价) | user_count(活跃用户数)
    - time_range_text: 时间范围描述，如"最近7天"/"本月"/"上月"，默认"最近30天"
    - group_by: 聚合粒度：day/week/month，留空自动判断（>90天用week，否则用day）

    返回：JSON格式，包含当期序列、上期序列、环比增长率、chart_data（前端折线图）
    """
    start_time = time.time()
    print(f"[工具] query_sales_trend 开始, metric={metric}, time={time_range_text}")

    valid_metrics = ["gmv", "order_count", "avg_order_amount", "user_count"]
    if metric not in valid_metrics:
        return f"不支持的指标: {metric}，支持: {', '.join(valid_metrics)}"

    # 解析时间范围
    time_range = parse_time_range(time_range_text)
    prev_range = get_previous_range(time_range)

    # 计算天数决定聚合粒度
    start_date = datetime.strptime(time_range["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(time_range["end_date"], "%Y-%m-%d").date()
    days = (end_date - start_date).days + 1

    if not group_by:
        group_by = _determine_group_by(days)

    # 查询当期和上期
    curr_series = _query_metric_series(metric, time_range["start_date"], time_range["end_date"], group_by)
    prev_series = _query_metric_series(metric, prev_range["start_date"], prev_range["end_date"], group_by)

    # 计算汇总
    curr_total = sum(p["value"] for p in curr_series)
    prev_total = sum(p["value"] for p in prev_series)
    change_pct = _calc_change(curr_total, prev_total)

    # 指标中文名
    metric_names = {
        "gmv": "销售额(GMV)",
        "order_count": "订单量",
        "avg_order_amount": "客单价",
        "user_count": "活跃用户数"
    }
    metric_unit = "元" if metric in ["gmv", "avg_order_amount"] else ""

    elapsed = time.time() - start_time
    print(f"[工具] query_sales_trend 完成, 耗时{elapsed:.3f}s, 当期{len(curr_series)}点, 上期{len(prev_series)}点")

    # 构造结果
    result = {
        "metric": metric,
        "metric_name": metric_names[metric],
        "time_range": time_range,
        "previous_range": prev_range,
        "group_by": group_by,
        "current_series": curr_series,
        "previous_series": prev_series,
        "current_total": round(curr_total, 2),
        "previous_total": round(prev_total, 2),
        "change_pct": change_pct,
        "change_direction": "up" if change_pct and change_pct > 0 else "down" if change_pct and change_pct < 0 else "flat",
        "elapsed_sec": round(elapsed, 3),
        "chart_data": {
            "type": "line",
            "title": f"{metric_names[metric]}趋势 - {time_range['label']}",
            "x_axis": [p["date"] for p in curr_series],
            "series": [
                {"name": f"当期({time_range['label']})", "data": [p["value"] for p in curr_series]},
                {"name": f"上期({prev_range['label']})", "data": [p["value"] for p in prev_series]}
            ],
            "unit": metric_unit
        }
    }

    return json.dumps(result, ensure_ascii=False, default=str)
