# 异常检测工具
# 设计目标：基于Z-Score识别业务异常
# - 7日/14日/30日滑动窗口对比
# - 单次SQL获取窗口内每日数据，内存计算统计量
# - 支持4个核心指标：GMV/订单量/客单价/评分

import time
import json
import math
from datetime import datetime, date, timedelta
from typing import Optional

from langchain.tools import tool

from ..database import get_db_connection


def _mean(values: list) -> float:
    if not values:
        return 0
    return sum(values) / len(values)


def _std(values: list) -> float:
    if len(values) < 2:
        return 0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def _query_daily_metric(metric: str, start: str, end: str) -> list:
    """查询时间窗口内每日指标值"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()

        if metric == "gmv":
            sql = """
                SELECT DATE(create_time) AS dt, SUM(order_amount) AS val
                FROM `order`
                WHERE pay_status = '1' AND is_delete = 0
                  AND create_time >= %s AND create_time <= %s
                GROUP BY DATE(create_time)
                ORDER BY dt
            """
        elif metric == "order_count":
            sql = """
                SELECT DATE(create_time) AS dt, COUNT(*) AS val
                FROM `order`
                WHERE is_delete = 0
                  AND create_time >= %s AND create_time <= %s
                GROUP BY DATE(create_time)
                ORDER BY dt
            """
        elif metric == "avg_order_amount":
            sql = """
                SELECT DATE(create_time) AS dt, AVG(order_amount) AS val
                FROM `order`
                WHERE pay_status = '1' AND is_delete = 0
                  AND create_time >= %s AND create_time <= %s
                GROUP BY DATE(create_time)
                ORDER BY dt
            """
        elif metric == "avg_score":
            sql = """
                SELECT DATE(create_time) AS dt, AVG(score) AS val
                FROM comment
                WHERE create_time >= %s AND create_time <= %s
                GROUP BY DATE(create_time)
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
        print(f"[工具] _query_daily_metric 异常: {e}")
        if conn:
            try:
                conn.close()
            except:
                pass
        return []


@tool
def detect_anomaly(
    metric: str = "gmv",
    window_days: int = 7
) -> str:
    """
    Z-Score异常检测：对比今日数据与过去N天的均值/标准差。

    参数：
    - metric: 监控指标：gmv(销售额) | order_count(订单量) | avg_order_amount(客单价) | avg_score(平均评分)
    - window_days: 参照窗口天数，默认7天，可选7/14/30

    返回：JSON格式，包含今日值、窗口均值、Z值、是否异常、异常方向 + chart_data
    """
    start_time = time.time()
    print(f"[工具] detect_anomaly 开始, metric={metric}, window={window_days}")

    valid_metrics = ["gmv", "order_count", "avg_order_amount", "avg_score"]
    if metric not in valid_metrics:
        return f"不支持的指标: {metric}"
    if window_days not in [7, 14, 30]:
        window_days = 7

    today = date.today()
    window_start = today - timedelta(days=window_days)
    # 窗口不含今天
    window_end = today - timedelta(days=1)

    # 查询窗口内每日数据
    window_series = _query_daily_metric(metric, window_start.isoformat(), window_end.isoformat())
    # 查询今日数据
    today_series = _query_daily_metric(metric, today.isoformat(), today.isoformat())

    elapsed_query = time.time() - start_time
    print(f"[工具] 异常检测数据查询完成, 耗时{elapsed_query:.3f}s")

    today_value = today_series[0]["value"] if today_series else 0
    window_values = [p["value"] for p in window_series]

    if len(window_values) < 3:
        return json.dumps({
            "metric": metric,
            "window_days": window_days,
            "today_value": round(today_value, 2),
            "window_mean": 0,
            "window_std": 0,
            "z_score": 0,
            "is_anomaly": False,
            "anomaly_level": "数据不足",
            "message": f"窗口内数据点不足({len(window_values)}/{window_days})，无法可靠计算异常",
            "elapsed_sec": round(time.time() - start_time, 3)
        }, ensure_ascii=False)

    mean = _mean(window_values)
    std = _std(window_values)

    if std == 0:
        z_score = 0
        is_anomaly = False
        anomaly_level = "正常"
        direction = "持平"
    else:
        z_score = (today_value - mean) / std
        abs_z = abs(z_score)
        if abs_z >= 3:
            is_anomaly = True
            anomaly_level = "严重异常"
        elif abs_z >= 2:
            is_anomaly = True
            anomaly_level = "异常"
        else:
            is_anomaly = False
            anomaly_level = "正常"
        direction = "偏高" if z_score > 0 else "偏低"

    # 指标中文名
    metric_names = {
        "gmv": "销售额(GMV)",
        "order_count": "订单量",
        "avg_order_amount": "客单价",
        "avg_score": "平均评分"
    }
    metric_unit = "元" if metric in ["gmv", "avg_order_amount"] else ("分" if metric == "avg_score" else "")

    elapsed = time.time() - start_time
    print(f"[工具] detect_anomaly 完成, 总耗时{elapsed:.3f}s, z_score={z_score:.2f}, anomaly={is_anomaly}")

    return json.dumps({
        "metric": metric,
        "metric_name": metric_names[metric],
        "window_days": window_days,
        "today": today.isoformat(),
        "today_value": round(today_value, 2),
        "window_mean": round(mean, 2),
        "window_std": round(std, 2),
        "z_score": round(z_score, 2),
        "is_anomaly": is_anomaly,
        "anomaly_level": anomaly_level,
        "direction": direction if is_anomaly else "持平",
        "window_series": window_series,
        "elapsed_sec": round(elapsed, 3),
        "chart_data": {
            "type": "line",
            "title": f"{metric_names[metric]}异常检测 - {window_days}日窗口",
            "x_axis": [p["date"] for p in window_series] + [today.isoformat()],
            "series": [{
                "name": metric_names[metric],
                "data": [p["value"] for p in window_series] + [today_value]
            }],
            "mark_line": {"y": mean, "name": "窗口均值"},
            "unit": metric_unit
        }
    }, ensure_ascii=False, default=str)


@tool
def anomaly_patrol() -> str:
    """
    异常巡检：一次性检测4个核心指标（GMV/订单量/客单价/评分），返回综合异常报告。
    适合作为日报的子模块。

    返回：JSON格式，包含所有指标的检测结果，并标注是否有异常
    """
    start_time = time.time()
    print(f"[工具] anomaly_patrol 开始 - 巡检4个指标")

    metrics = ["gmv", "order_count", "avg_order_amount", "avg_score"]
    results = []

    for m in metrics:
        # 直接调用内部函数，避免tool装饰器的开销
        result_str = detect_anomaly.invoke({"metric": m, "window_days": 7})
        try:
            result = json.loads(result_str)
            results.append(result)
        except:
            results.append({"metric": m, "error": result_str})

    has_anomaly = any(r.get("is_anomaly", False) for r in results if isinstance(r, dict))
    anomaly_count = sum(1 for r in results if isinstance(r, dict) and r.get("is_anomaly"))

    elapsed = time.time() - start_time
    print(f"[工具] anomaly_patrol 完成, 总耗时{elapsed:.3f}s, 异常指标数{anomaly_count}/{len(metrics)}")

    return json.dumps({
        "patrol_type": "daily_anomaly_check",
        "metrics_checked": metrics,
        "has_anomaly": has_anomaly,
        "anomaly_count": anomaly_count,
        "results": results,
        "elapsed_sec": round(elapsed, 3)
    }, ensure_ascii=False, default=str)
