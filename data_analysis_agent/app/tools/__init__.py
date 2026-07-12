# 数据分析Agent工具集
# Tool注册表：所有Tool通过all_tool_funcs导出供Agent使用
# 分类：
#   1. SQL查询类：execute_analytics_sql（Text2SQL沙箱）
#   2. 趋势分析类：query_sales_trend
#   3. 排行类：query_product_ranking, query_category_brand_ranking
#   4. 用户分析类：analyze_user_rfm
#   5. 异常检测类：detect_anomaly, anomaly_patrol
#   6. 评论分析类：analyze_product_comments, find_low_rated_products
#   7. 报告类：generate_daily_report, generate_weekly_report
#   8. Skills：run_skill（预定义Tool调用链）

from .sql_query_tool import execute_analytics_sql
from .trend_analysis_tool import query_sales_trend
from .ranking_tool import query_product_ranking, query_category_brand_ranking
from .rfm_tool import analyze_user_rfm
from .anomaly_tool import detect_anomaly, anomaly_patrol
from .comment_analysis_tool import analyze_product_comments, find_low_rated_products
from .report_tool import generate_daily_report, generate_weekly_report
from .skills import run_skill, match_skill

# 所有Tool函数列表（供Agent.bind_tools使用）
all_tool_funcs = [
    # SQL查询
    execute_analytics_sql,
    # 趋势分析
    query_sales_trend,
    # 排行
    query_product_ranking,
    query_category_brand_ranking,
    # 用户分析
    analyze_user_rfm,
    # 异常检测
    detect_anomaly,
    anomaly_patrol,
    # 评论分析
    analyze_product_comments,
    find_low_rated_products,
    # 报告
    generate_daily_report,
    generate_weekly_report,
    # Skills
    run_skill,
]

# Tool名称到函数的映射（供Skill内部调用）
TOOL_NAME_MAP = {t.name: t for t in all_tool_funcs}
