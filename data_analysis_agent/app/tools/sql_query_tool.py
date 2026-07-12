# 安全SQL查询工具（Text2SQL沙箱）
# 设计目标：让LLM生成SQL查询分析数据，同时保证安全和性能
# - 只允许SELECT + 聚合 + LIMIT
# - 强制时间范围（防止全表扫描）
# - 限制最大返回行数（SQL_MAX_ROWS=1000）
# - 查询超时（SQL_QUERY_TIMEOUT=10s）

import re
import time
import json
import hashlib
from typing import Optional

from langchain.tools import tool

from ..database import get_db_connection
from ..config import SQL_QUERY_TIMEOUT, SQL_MAX_ROWS, SQL_CACHE_ENABLED, SQL_CACHE_TTL, REDIS_URL
from .time_utils import parse_time_range


# ======================= Redis查询缓存 =======================
# 设计目标：相同SQL在5分钟内不重复查数据库，降低DB压力
# - 用MD5(normalized_sql)作为缓存key
# - TTL 300秒（5分钟），兼顾数据新鲜度和性能
# - Redis不可用时自动降级到直接查询

_redis_client = None
_redis_available = None  # None=未检测, True=可用, False=不可用


def _get_redis_client():
    """获取同步Redis客户端（懒加载，失败后不再重试）"""
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=2)
        _redis_client.ping()  # 测试连接
        _redis_available = True
        print("[缓存] Redis客户端已初始化")
        return _redis_client
    except Exception as e:
        _redis_available = False
        print(f"[缓存] Redis不可用，降级为直接查询: {e}")
        return None


def _get_cache_key(sql: str) -> str:
    """根据SQL生成缓存key（归一化后MD5）"""
    # 归一化：去前后空格 + 统一小写 + 压缩多余空格
    normalized = re.sub(r'\s+', ' ', sql.strip().lower())
    md5 = hashlib.md5(normalized.encode('utf-8')).hexdigest()
    return f"sql_cache:{md5}"


def _get_cached_result(cache_key: str) -> Optional[str]:
    """从Redis读取缓存"""
    if not SQL_CACHE_ENABLED:
        return None
    client = _get_redis_client()
    if not client:
        return None
    try:
        cached = client.get(cache_key)
        if cached:
            print(f"[缓存] 命中: {cache_key[:30]}...")
        return cached
    except Exception as e:
        print(f"[缓存] 读取失败: {e}")
        return None


def _set_cached_result(cache_key: str, result: str):
    """写入Redis缓存"""
    if not SQL_CACHE_ENABLED:
        return
    client = _get_redis_client()
    if not client:
        return
    try:
        client.setex(cache_key, SQL_CACHE_TTL, result)
    except Exception as e:
        print(f"[缓存] 写入失败: {e}")


# ======================= SQL安全校验 =======================
# 危险关键词黑名单
DANGEROUS_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "replace", "grant", "revoke", "lock", "unlock", "call", "exec",
    "load_file", "outfile", "dumpfile", "into"
]

# 允许的聚合函数
ALLOWED_AGG_FUNCS = ["sum", "count", "avg", "max", "min", "distinct"]


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    校验SQL安全性，返回(是否通过, 原因)
    """
    if not sql:
        return False, "SQL为空"

    s = sql.strip().lower()

    # 必须以SELECT开头
    if not s.startswith("select"):
        return False, "只允许SELECT查询语句"

    # 禁止危险关键词
    for kw in DANGEROUS_KEYWORDS:
        # 用单词边界匹配，避免误伤字段名
        pattern = r"\b" + kw + r"\b"
        if re.search(pattern, s):
            return False, f"禁止使用关键词: {kw}"

    # 禁止分号（防止多语句注入）
    if ";" in s.rstrip(";"):
        return False, "禁止使用分号"

    # 禁止注释（防止注释注入）
    if "--" in s or "/*" in s or "#" in s:
        return False, "禁止使用注释"

    # LIMIT校验：如果已有LIMIT，检查大小；如果没有，后续自动添加
    m = re.search(r"limit\s+(\d+)", s)
    if m:
        limit_val = int(m.group(1))
        if limit_val > SQL_MAX_ROWS:
            return False, f"LIMIT不能超过{SQL_MAX_ROWS}"

    return True, "通过"


def ensure_limit(sql: str, default_limit: int = 100) -> str:
    """如果SQL没有LIMIT子句，自动添加"""
    if re.search(r"\blimit\b", sql, re.IGNORECASE):
        return sql
    return sql.rstrip(";") + f" LIMIT {default_limit}"


def escape_table_names(sql: str) -> str:
    """自动给MySQL保留字表名加反引号（如order→`order`）"""
    # order是MySQL保留字，必须加反引号
    # 匹配 FROM order 或 JOIN order 或 INTO order（不在反引号内）
    sql = re.sub(r'(?<!`)\bFROM\s+order\b(?!`)', 'FROM `order`', sql, flags=re.IGNORECASE)
    sql = re.sub(r'(?<!`)\bJOIN\s+order\b(?!`)', 'JOIN `order`', sql, flags=re.IGNORECASE)
    sql = re.sub(r'(?<!`)\bINTO\s+order\b(?!`)', 'INTO `order`', sql, flags=re.IGNORECASE)
    sql = re.sub(r'(?<!`)\bUPDATE\s+order\b(?!`)', 'UPDATE `order`', sql, flags=re.IGNORECASE)
    return sql


def inject_time_range(sql: str, time_range: dict) -> str:
    """
    如果SQL的WHERE子句中没有时间范围条件，自动注入create_time过滤
    （仅对order/comment/order_goods表生效）
    多表JOIN时使用表前缀避免字段歧义（Column 'create_time' is ambiguous）
    """
    s = sql.lower()
    # 只检测WHERE子句中是否已有create_time条件（避免SELECT/GROUP BY中的create_time误判）
    where_match = re.search(r'\bwhere\b\s+(.+?)(?:\bgroup by\b|\border by\b|\blimit\b|$)', s, re.DOTALL)
    if where_match and "create_time" in where_match.group(1):
        return sql  # WHERE中已有create_time条件，不再注入

    # 检查SQL是否涉及需要时间过滤的表
    has_order = "`order`" in s
    has_order_goods = "order_goods" in s
    has_comment = re.search(r"\bcomment\b", s) is not None
    if not (has_order or has_order_goods or has_comment):
        return sql

    # 多表JOIN时，create_time字段可能歧义，需要用表前缀
    # 优先用`order`.create_time（销售/订单查询最常见），其次comment.create_time
    has_join = re.search(r"\bjoin\b", s) is not None
    if has_join and has_order:
        time_col = "`order`.create_time"
    elif has_join and has_comment and not has_order:
        time_col = "comment.create_time"
    elif has_join and has_order_goods and not has_order and not has_comment:
        time_col = "order_goods.create_time"
    else:
        time_col = "create_time"

    start = time_range["start_date"]
    end = time_range["end_date"]
    time_cond = f"{time_col} >= '{start} 00:00:00' AND {time_col} <= '{end} 23:59:59'"

    # 在WHERE前插入条件；如果没有WHERE，则在ORDER BY/LIMIT前插入WHERE
    if "where" in s:
        # 已有WHERE，加AND
        new_sql = re.sub(
            r"\bwhere\b",
            f"WHERE {time_cond} AND ",
            sql,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # 没有WHERE，在ORDER BY/GROUP BY/LIMIT前插入WHERE
        for kw in ["order by", "group by", "limit"]:
            if kw in s:
                new_sql = re.sub(
                    rf"\b{kw}\b",
                    f"WHERE {time_cond} {kw} ",
                    sql,
                    count=1,
                    flags=re.IGNORECASE
                )
                break
        else:
            # 没有任何子句，直接追加到末尾
            new_sql = sql.rstrip(";") + f" WHERE {time_cond}"

    return new_sql


def fix_ambiguous_columns(sql: str) -> str:
    """
    修复多表JOIN时的字段歧义：给裸的create_time加上表前缀。
    处理LLM生成的SELECT/GROUP BY/ORDER BY中的裸create_time。
    在inject_time_range之后调用（inject_time_range注入的create_time已有前缀）。
    """
    s = sql.lower()

    # 检测是否有多表JOIN
    if not re.search(r"\bjoin\b", s):
        return sql

    # 检测涉及哪些有create_time的表
    has_order = "`order`" in s
    has_order_goods = "order_goods" in s
    has_comment = re.search(r"\bcomment\b", s) is not None

    # 只有多表JOIN且涉及多个有create_time的表时才需要修复
    tables_with_create_time = sum([has_order, has_order_goods, has_comment])
    if tables_with_create_time < 2:
        return sql

    # 决定用哪个表的前缀（优先order表，与inject_time_range一致）
    if has_order:
        prefix = "`order`"
    elif has_comment:
        prefix = "comment"
    else:
        prefix = "order_goods"

    # 给裸的create_time加前缀（不处理已有前缀的，如`order`.create_time或order.create_time）
    # 正则：匹配 create_time，前面不是 . 或字母数字下划线
    pattern = r'(?<![.\w])create_time'
    sql = re.sub(pattern, f'{prefix}.create_time', sql, flags=re.IGNORECASE)

    return sql


def _is_date_value(val) -> bool:
    """判断值是否像日期（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）"""
    if not isinstance(val, str):
        return False
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?$', val.strip()))


def _is_numeric_value(val) -> bool:
    """判断值是否为数字"""
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def _generate_chart_from_result(columns: list, rows: list, time_range_label: str = "") -> dict:
    """
    根据SQL查询结果自动生成chart_data（供前端ECharts渲染）。
    启发式规则：
    - 2列，第一列是日期 → 折线图（趋势）
    - 2列，第一列非日期 → 柱状图（对比）
    - 3+列，第一列是日期 → 多系列折线图
    - 3+列，第一列非日期 → 多系列柱状图
    - 1列或无法判断 → 不生成图表
    注意：rows可能是dict列表（DictCursor）或tuple列表（普通游标），需兼容处理。
    """
    if not columns or not rows or len(columns) < 2:
        return None

    # 统一将行数据转为list（兼容dict和tuple）
    def row_to_list(r):
        if isinstance(r, dict):
            return [r.get(c) for c in columns]
        return list(r) if r else []

    # 限制图表数据点（最多15个，避免过于密集）
    chart_rows = [row_to_list(r) for r in rows[:15]]

    first_col_name = str(columns[0])
    first_col_values = [r[0] for r in chart_rows if r and len(r) > 0]
    is_date_col = any(_is_date_value(v) for v in first_col_values[:3])

    # 第一列作为x轴标签
    x_axis = [str(v)[:20] for v in first_col_values]

    # 剩余列作为数据系列
    series_list = []
    for col_idx in range(1, len(columns)):
        col_name = str(columns[col_idx])
        col_data = []
        for r in chart_rows:
            if r and len(r) > col_idx:
                val = r[col_idx]
                if _is_numeric_value(val):
                    col_data.append(float(val))
                else:
                    col_data.append(0)
            else:
                col_data.append(0)
        series_list.append({"name": col_name, "data": col_data})

    if not series_list:
        return None

    # 判断是否有"元"相关列（用于单位标注）
    has_money = any(kw in str(columns).lower() for kw in ["gmv", "销售额", "金额", "收入", "客单价", "revenue", "amount"])
    unit = "元" if has_money else ""

    chart_type = "line" if is_date_col else "bar"
    title_suffix = time_range_label or ""

    return {
        "type": chart_type,
        "title": f"{first_col_name}分析" + (f" - {title_suffix}" if title_suffix else ""),
        "x_axis": x_axis,
        "series": series_list,
        "unit": unit
    }


@tool
def execute_analytics_sql(sql: str, time_range_text: Optional[str] = None) -> str:
    """
    执行数据分析SQL查询。只允许SELECT语句，必须包含LIMIT，最大返回1000行。

    使用规则：
    1. 只允许SELECT + 聚合函数(SUM/COUNT/AVG/MAX/MIN) + GROUP BY
    2. 禁止INSERT/UPDATE/DELETE/DROP等写操作
    3. 必须包含LIMIT子句
    4. 涉及order/order_goods/comment表时，自动注入create_time时间范围
    5. 查询超时10秒自动终止

    参数：
    - sql: 完整的SELECT SQL语句
    - time_range_text: 可选，时间范围描述（如"最近7天"/"本月"），用于自动注入时间过滤

    返回：JSON格式查询结果，包含columns和rows
    """
    start_time = time.time()
    print(f"[工具] execute_analytics_sql 开始, sql={sql[:80]}...")

    # 1. 安全校验
    ok, reason = validate_sql(sql)
    if not ok:
        return f"SQL校验失败: {reason}"

    # 2. 自动添加LIMIT（如果没有）
    final_sql = ensure_limit(sql, default_limit=100)

    # 2.5 自动给保留字表名加反引号
    final_sql = escape_table_names(final_sql)

    # 3. 注入时间范围
    if time_range_text:
        try:
            tr = parse_time_range(time_range_text)
            final_sql = inject_time_range(final_sql, tr)
            print(f"[工具] 注入时间范围: {tr['label']} ({tr['start_date']} ~ {tr['end_date']})")
        except Exception as e:
            print(f"[工具] 时间范围解析失败: {e}")

    # 3.1 修复多表JOIN时的字段歧义（给裸create_time加表前缀）
    final_sql = fix_ambiguous_columns(final_sql)

    # 3.5 查询Redis缓存（命中则直接返回，跳过数据库查询）
    cache_key = _get_cache_key(final_sql)
    cached = _get_cached_result(cache_key)
    if cached:
        try:
            result = json.loads(cached)
            result["cached"] = True
            result["elapsed_sec"] = round(time.time() - start_time, 3)
            # 旧缓存可能没有chart_data，补生成
            if "chart_data" not in result and result.get("columns") and result.get("rows"):
                try:
                    cd = _generate_chart_from_result(result["columns"], result["rows"], time_range_text or "")
                    if cd:
                        result["chart_data"] = cd
                except Exception:
                    pass
            print(f"[工具] 缓存命中，跳过数据库查询")
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception:
            pass  # 缓存数据损坏，继续查数据库

    # 4. 执行查询
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return "数据库连接失败"

        cursor = conn.cursor()

        # 设置查询超时（通过MAX_STATEMENT_TIME，单位毫秒）
        try:
            cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={SQL_QUERY_TIMEOUT * 1000}")
        except Exception:
            pass  # 某些MySQL版本不支持，忽略

        cursor.execute(final_sql)
        rows = cursor.fetchall()

        # 获取列名
        columns = []
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]

        elapsed = time.time() - start_time
        print(f"[工具] SQL执行耗时: {elapsed:.3f}s, 返回{len(rows)}行")

        # 5. 格式化结果
        if not rows:
            return json.dumps({
                "columns": columns,
                "rows": [],
                "row_count": 0,
                "elapsed_sec": round(elapsed, 3),
                "message": "查询结果为空"
            }, ensure_ascii=False, default=str)

        # 限制返回行数（双保险）
        if len(rows) > SQL_MAX_ROWS:
            rows = rows[:SQL_MAX_ROWS]

        result = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "elapsed_sec": round(elapsed, 3),
            "cached": False
        }

        # 6.1 自动生成chart_data（根据结果结构推断图表类型）
        try:
            time_label = time_range_text or ""
            chart_data = _generate_chart_from_result(columns, rows, time_label)
            if chart_data:
                result["chart_data"] = chart_data
        except Exception as e:
            import traceback
            print(f"[工具] 图表生成失败(不影响查询): {type(e).__name__}: {e}")
            traceback.print_exc()

        # 7. 写入Redis缓存（只缓存成功的结果，含chart_data）
        try:
            _set_cached_result(cache_key, json.dumps(result, ensure_ascii=False, default=str))
        except Exception:
            pass  # 缓存写入失败不影响主流程

        cursor.close()
        conn.close()
        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        import traceback
        traceback.print_exc()
        if conn:
            try:
                conn.close()
            except:
                pass
        elapsed = time.time() - start_time
        return f"SQL执行失败({elapsed:.2f}s): {str(e)}"
