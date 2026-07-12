import sys
sys.path.insert(0, '.')
from app.tools.sql_query_tool import execute_analytics_sql

sql = "SELECT SUM(order_amount) as total FROM `order` WHERE pay_status='1' AND is_delete=0 LIMIT 1"
result = execute_analytics_sql.invoke({"sql": sql, "time_range_text": "最近30天"})
print("结果:", result[:500])
