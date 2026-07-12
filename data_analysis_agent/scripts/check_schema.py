# -*- coding: utf-8 -*-
"""查看数据库表结构"""
import pymysql

conn = pymysql.connect(host='localhost', user='root', password='123456', database='muxi_shop', charset='utf8mb4')
cur = conn.cursor()

for t in ['user', 'goods', 'order', 'order_goods', 'comment']:
    cur.execute(f"DESCRIBE `{t}`")
    print(f"=== {t} ===")
    for r in cur.fetchall():
        print(f"  {r[0]} | {r[1]} | key={r[3]}")
    cur.execute(f"SELECT COUNT(*) FROM `{t}`")
    print(f"  数据量: {cur.fetchone()[0]}")
    print()

# 查看商品表的前3条数据
cur.execute("SELECT * FROM goods LIMIT 3")
print("=== goods 前3条 ===")
for r in cur.fetchall():
    print(f"  {r}")

# 查看order表的前3条数据
cur.execute("SELECT * FROM `order` LIMIT 3")
print("\n=== order 前3条 ===")
for r in cur.fetchall():
    print(f"  {r}")

# 查看comment表的前3条
cur.execute("SELECT * FROM comment LIMIT 3")
print("\n=== comment 前3条 ===")
for r in cur.fetchall():
    print(f"  {r}")

conn.close()
