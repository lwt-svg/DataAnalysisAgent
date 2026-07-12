# 时间解析工具（所有Tool共用）

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


def parse_time_range(text: str) -> Dict[str, str]:
    """
    解析用户输入中的时间范围，返回start_date和end_date（YYYY-MM-DD格式）

    支持的表达：
    - 今天/今日
    - 昨天/昨日
    - 最近N天 / 过去N天 / 近N天
    - 本周 / 上周
    - 本月 / 上个月 / 上月
    - 今年
    - 无时间词 → 默认最近30天
    """
    if not text:
        return _default_range()

    t = str(text).strip()
    today = datetime.now().date()

    # 今天/今日
    if any(k in t for k in ["今天", "今日", "今日的", "本日"]):
        return {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "label": "今天"
        }

    # 昨天/昨日
    if any(k in t for k in ["昨天", "昨日"]):
        yesterday = today - timedelta(days=1)
        return {
            "start_date": yesterday.isoformat(),
            "end_date": yesterday.isoformat(),
            "label": "昨天"
        }

    # 最近N天 / 过去N天 / 近N天
    m = re.search(r'(?:最近|过去|近|过去)\s*(\d+)\s*天', t)
    if m:
        days = int(m.group(1))
        start = today - timedelta(days=days - 1)
        return {
            "start_date": start.isoformat(),
            "end_date": today.isoformat(),
            "label": f"最近{days}天"
        }

    # 本周
    if "本周" in t or "这周" in t:
        monday = today - timedelta(days=today.weekday())
        return {
            "start_date": monday.isoformat(),
            "end_date": today.isoformat(),
            "label": "本周"
        }

    # 上周
    if "上周" in t:
        monday = today - timedelta(days=today.weekday() + 7)
        sunday = monday + timedelta(days=6)
        return {
            "start_date": monday.isoformat(),
            "end_date": sunday.isoformat(),
            "label": "上周"
        }

    # 本月
    if "本月" in t or "这个月" in t:
        first_day = today.replace(day=1)
        return {
            "start_date": first_day.isoformat(),
            "end_date": today.isoformat(),
            "label": "本月"
        }

    # 上个月/上月
    if "上个月" in t or "上月" in t:
        first_of_this_month = today.replace(day=1)
        last_of_prev = first_of_this_month - timedelta(days=1)
        first_of_prev = last_of_prev.replace(day=1)
        return {
            "start_date": first_of_prev.isoformat(),
            "end_date": last_of_prev.isoformat(),
            "label": "上个月"
        }

    # 今年
    if "今年" in t:
        first_day = today.replace(month=1, day=1)
        return {
            "start_date": first_day.isoformat(),
            "end_date": today.isoformat(),
            "label": "今年"
        }

    # 无时间词 → 默认最近30天
    return _default_range()


def _default_range(days: int = 30) -> Dict[str, str]:
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    return {
        "start_date": start.isoformat(),
        "end_date": today.isoformat(),
        "label": f"最近{days}天"
    }


def get_previous_range(time_range: Dict[str, str]) -> Dict[str, str]:
    """
    获取上一个对比周期（用于环比计算）
    例如：今天是最近7天 → 返回前7天
    """
    start = datetime.strptime(time_range["start_date"], "%Y-%m-%d").date()
    end = datetime.strptime(time_range["end_date"], "%Y-%m-%d").date()
    period_days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_days - 1)
    return {
        "start_date": prev_start.isoformat(),
        "end_date": prev_end.isoformat(),
        "label": f"上一周期"
    }
