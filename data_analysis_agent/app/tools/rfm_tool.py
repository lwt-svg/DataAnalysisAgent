# RFM用户分群工具
# 设计目标：高效完成RFM分群分析
# - 单次SQL查询获取所有用户的R/F/M三个指标（避免3次查询）
# - 内存中完成分群计算（数据量小时效率高）
# - 返回8类用户分群结果 + chart_data

import time
import json
from datetime import datetime, date
from typing import Optional

from langchain.tools import tool

from ..database import get_db_connection


@tool
def analyze_user_rfm(
    time_range_text: str = "最近30天",
    reference_date: Optional[str] = None
) -> str:
    """
    RFM用户分群分析，识别核心用户、活跃用户、流失用户等。

    参数：
    - time_range_text: 分析时间范围，默认最近30天
    - reference_date: 参照日期（YYYY-MM-DD），默认今天

    返回：JSON格式分群结果，包含8类用户数量、占比、平均消费金额 + chart_data（饼图）
    """
    start_time = time.time()
    print(f"[工具] analyze_user_rfm 开始, time={time_range_text}")

    # 解析参照日期
    if reference_date:
        try:
            ref_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
        except:
            ref_date = date.today()
    else:
        ref_date = date.today()

    # 解析时间范围（用parse_time_range获得start_date）
    from .time_utils import parse_time_range
    tr = parse_time_range(time_range_text)
    start_date = tr["start_date"]

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return "数据库连接失败"
        cursor = conn.cursor()

        # 一次性查询所有用户的R/F/M三个指标
        # R: 最近一次购买距今天数
        # F: 时间范围内购买次数
        # M: 时间范围内消费金额
        sql = """
            SELECT
                o.email,
                MAX(o.create_time) AS last_order_time,
                COUNT(DISTINCT o.trade_no) AS frequency,
                SUM(o.order_amount) AS monetary
            FROM `order` o
            WHERE o.is_delete = 0
              AND o.pay_status = '1'
              AND o.create_time >= %s
              AND o.create_time <= %s
            GROUP BY o.email
        """
        cursor.execute(sql, (f"{start_date} 00:00:00", f"{ref_date.isoformat()} 23:59:59"))
        rows = cursor.fetchall()

        elapsed_query = time.time() - start_time
        print(f"[工具] RFM数据查询完成, 耗时{elapsed_query:.3f}s, 用户数{len(rows)}")

        cursor.close()
        conn.close()

        if not rows:
            return json.dumps({
                "time_range": tr,
                "reference_date": ref_date.isoformat(),
                "total_users": 0,
                "segments": [],
                "message": "该时间范围内无支付订单数据",
                "elapsed_sec": round(elapsed_query, 3)
            }, ensure_ascii=False, default=str)

        # 计算每个用户的R值（天数）
        ref_dt = datetime.combine(ref_date, datetime.min.time())
        user_data = []
        for r in rows:
            last_time = r["last_order_time"]
            if isinstance(last_time, str):
                last_time = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
            elif hasattr(last_time, 'to_pydatetime'):
                last_time = last_time.to_pydatetime()

            recency_days = (ref_dt - last_time).days
            user_data.append({
                "email": r["email"],
                "recency": recency_days,
                "frequency": int(r["frequency"]),
                "monetary": float(r["monetary"]) if r["monetary"] else 0
            })

        # 计算R/F/M的中位数作为阈值
        recencies = sorted([u["recency"] for u in user_data])
        frequencies = sorted([u["frequency"] for u in user_data])
        monetaries = sorted([u["monetary"] for u in user_data])

        n = len(user_data)
        r_threshold = recencies[n // 2]  # R越小越好，<=阈值为"好"
        f_threshold = frequencies[n // 2]  # F越大越好，>=阈值为"好"
        m_threshold = monetaries[n // 2]  # M越大越好，>=阈值为"好"

        # 分群
        # 8种组合：(R高低)(F高低)(M高低)
        segments_def = {
            "重要价值用户": ("high", "high", "high"),
            "重要发展用户": ("high", "low", "high"),
            "重要保持用户": ("low", "high", "high"),
            "重要挽留用户": ("low", "low", "high"),
            "一般价值用户": ("high", "high", "low"),
            "一般发展用户": ("high", "low", "low"),
            "一般保持用户": ("low", "high", "low"),
            "一般挽留用户": ("low", "low", "low"),
        }

        segment_users = {k: [] for k in segments_def}
        for u in user_data:
            r_high = u["recency"] <= r_threshold
            f_high = u["frequency"] >= f_threshold
            m_high = u["monetary"] >= m_threshold

            key = ("high" if r_high else "low", "high" if f_high else "low", "high" if m_high else "low")
            for seg_name, seg_key in segments_def.items():
                if key == seg_key:
                    segment_users[seg_name].append(u)
                    break

        # 计算每个分群的统计
        total = len(user_data)
        segments_result = []
        for seg_name, users in segment_users.items():
            if not users:
                segments_result.append({
                    "segment": seg_name,
                    "user_count": 0,
                    "percentage": 0,
                    "avg_recency": 0,
                    "avg_frequency": 0,
                    "avg_monetary": 0,
                    "total_monetary": 0
                })
                continue

            segments_result.append({
                "segment": seg_name,
                "user_count": len(users),
                "percentage": round(len(users) / total * 100, 1),
                "avg_recency": round(sum(u["recency"] for u in users) / len(users), 1),
                "avg_frequency": round(sum(u["frequency"] for u in users) / len(users), 1),
                "avg_monetary": round(sum(u["monetary"] for u in users) / len(users), 2),
                "total_monetary": round(sum(u["monetary"] for u in users), 2)
            })

        # 按用户数倒序
        segments_result.sort(key=lambda x: x["user_count"], reverse=True)

        elapsed = time.time() - start_time
        print(f"[工具] analyze_user_rfm 完成, 总耗时{elapsed:.3f}s")

        return json.dumps({
            "time_range": tr,
            "reference_date": ref_date.isoformat(),
            "total_users": total,
            "thresholds": {
                "recency_days": r_threshold,
                "frequency_count": f_threshold,
                "monetary_yuan": round(m_threshold, 2)
            },
            "segments": segments_result,
            "elapsed_sec": round(elapsed, 3),
            "chart_data": {
                "type": "pie",
                "title": f"用户分群(RFM)分布 - {tr['label']}",
                "data": [{"name": s["segment"], "value": s["user_count"]} for s in segments_result if s["user_count"] > 0]
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
        return f"RFM分析时出错: {str(e)}"
