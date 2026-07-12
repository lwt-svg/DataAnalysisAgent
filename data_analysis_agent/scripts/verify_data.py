# -*- coding: utf-8 -*-
"""验证测试数据"""
import pymysql

conn = pymysql.connect(host='localhost', user='root', password='123456', database='muxi_shop', charset='utf8mb4')
cur = conn.cursor()

print("========== 测试数据验证 ==========")

# 用户
cur.execute("SELECT COUNT(*) FROM user")
print(f"\n用户总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM user WHERE email LIKE 'test_agent_%'")
print(f"  其中测试用户: {cur.fetchone()[0]}")
cur.execute("SELECT id, name, email, create_time FROM user WHERE email LIKE 'test_agent_%' LIMIT 5")
print("  测试用户示例:")
for r in cur.fetchall():
    print(f"    id={r[0]}, name={r[1]}, email={r[2]}, create_time={r[3]}")

# 订单
cur.execute("SELECT COUNT(*) FROM `order`")
print(f"\n订单总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM `order` WHERE trade_no LIKE 'TEST%'")
print(f"  其中测试订单: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM `order` WHERE create_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
print(f"  最近30天订单: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM `order` WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
print(f"  最近7天订单: {cur.fetchone()[0]}")
cur.execute("SELECT pay_status, COUNT(*) FROM `order` WHERE trade_no LIKE 'TEST%' GROUP BY pay_status")
print("  测试订单支付状态分布:")
for r in cur.fetchall():
    status = {'0': '待支付', '1': '已支付', '2': '已取消'}.get(r[0], r[0])
    print(f"    {status}: {r[1]}")

# 订单商品
cur.execute("SELECT COUNT(*) FROM order_goods WHERE trade_no LIKE 'TEST%'")
print(f"\n测试订单商品: {cur.fetchone()[0]}")

# 评论
cur.execute("SELECT COUNT(*) FROM comment")
print(f"\n评论总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM comment WHERE create_time >= DATE_SUB(NOW(), INTERVAL 90 DAY)")
print(f"  最近90天评论: {cur.fetchone()[0]}")

# 订单时间分布
cur.execute("""
    SELECT DATE(create_time) as d, COUNT(*) as c
    FROM `order` WHERE trade_no LIKE 'TEST%'
    GROUP BY DATE(create_time) ORDER BY d DESC LIMIT 7
""")
print("\n最近7天订单分布:")
for r in cur.fetchall():
    print(f"    {r[0]}: {r[1]}个订单")

conn.close()
