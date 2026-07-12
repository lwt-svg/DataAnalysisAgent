# -*- coding: utf-8 -*-
"""
数据分析Agent测试数据生成脚本
生成最近90天的模拟订单数据，用于测试数据分析Agent的各项功能

使用方法:
    python scripts/generate_test_data.py           # 生成数据
    python scripts/generate_test_data.py --clean    # 清除生成的测试数据

生成的数据特点:
    - 100个新用户，注册时间分布在最近180天
    - 800个订单，时间分布在最近90天
    - 订单有合理的支付状态分布(70%已支付/20%待支付/10%已取消)
    - 周末订单多、工作日少（有周期性波动）
    - 最近30天订单比之前多（有增长趋势）
    - 用户消费频次分布合理（支持RFM分群）
    - 已支付订单30%概率有评论
"""

import pymysql
import random
import argparse
from datetime import datetime, timedelta
from decimal import Decimal

# ========== 配置 ==========
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "muxi_shop",
    "charset": "utf8mb4"
}

# 数据量配置
NUM_USERS = 100          # 新增用户数
NUM_ORDERS = 800         # 新增订单数
COMMENT_RATE = 0.30      # 已支付订单生成评论的概率

# 标记前缀，方便清理
TEST_FLAG = "test_agent_"

# ========== 商品池（从数据库取真实商品） ==========
def get_goods_pool(cursor):
    """获取数据库中的真实商品列表"""
    cursor.execute("SELECT sku_id, name, p_price, jd_price, mk_price, main_brand, main_category FROM goods WHERE p_price > 0 LIMIT 200")
    goods = cursor.fetchall()
    print(f"[数据源] 从goods表加载 {len(goods)} 个真实商品")
    return goods


# ========== 用户生成 ==========
def generate_users(cursor, conn, count):
    """生成模拟用户"""
    now = datetime.now()
    existing_emails = set()

    # 获取已有邮箱
    cursor.execute("SELECT email FROM user")
    for r in cursor.fetchall():
        existing_emails.add(r[0])

    created = 0
    for i in range(count):
        email = f"{TEST_FLAG}user{i+1:03d}@test.com"
        if email in existing_emails:
            continue

        # 注册时间：最近180天内，近期注册的更多
        days_ago = int(random.expovariate(1/60))  # 指数分布，平均60天前
        days_ago = min(days_ago, 180)
        create_time = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        name = f"测试用户{i+1:03d}"
        mobile = f"138{random.randint(10000000, 99999999)}"
        gender = random.choice(["男", "女", "保密"])

        cursor.execute(
            "INSERT INTO user (name, birthday, mobile, gender, email, password, create_time) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name, create_time, mobile, gender, email, "test_hash", create_time)
        )
        created += 1

    conn.commit()
    print(f"[用户] 生成 {created} 个测试用户")
    return created


# ========== 订单生成 ==========
def generate_orders(cursor, conn, goods_pool, user_count):
    """生成模拟订单"""
    now = datetime.now()
    all_test_emails = [f"{TEST_FLAG}user{i+1:03d}@test.com" for i in range(user_count)]

    # 也加入一些已有用户邮箱，让数据更真实
    cursor.execute("SELECT email FROM user WHERE email NOT LIKE %s", (f"{TEST_FLAG}%",))
    existing_emails = [r[0] for r in cursor.fetchall()][:5]
    all_emails = all_test_emails + existing_emails

    # 用户消费频次权重：20%高频、30%中频、50%低频
    user_frequency = {}
    for email in all_emails:
        rand = random.random()
        if rand < 0.20:
            user_frequency[email] = random.randint(8, 20)   # 高频用户
        elif rand < 0.50:
            user_frequency[email] = random.randint(3, 7)    # 中频用户
        else:
            user_frequency[email] = random.randint(1, 2)    # 低频用户

    # 生成订单时间列表：最近90天
    order_times = []
    for days_ago in range(90):
        date = now - timedelta(days=days_ago)
        weekday = date.weekday()

        # 周末订单多，工作日少
        if weekday >= 5:
            base_count = 12  # 周末
        else:
            base_count = 6   # 工作日

        # 最近30天有增长趋势
        if days_ago < 30:
            base_count = int(base_count * 1.5)
        elif days_ago < 60:
            base_count = int(base_count * 1.2)

        # 随机波动
        count = max(1, int(base_count * random.uniform(0.6, 1.4)))

        for _ in range(count):
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,3,5,8,10,12,15,18,20,22,20,18,15,12,8,5,3,2,1]
            )[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            order_time = date.replace(hour=hour, minute=minute, second=second,
                                       microsecond=random.randint(0, 999999))
            order_times.append(order_time)

    # 取需要的数量
    random.shuffle(order_times)
    order_times = sorted(order_times[:NUM_ORDERS])

    print(f"[订单] 计划生成 {len(order_times)} 个订单")

    # 按权重选择用户
    weighted_emails = []
    for email, freq in user_frequency.items():
        weighted_emails.extend([email] * freq)

    order_count = 0
    og_count = 0
    comment_count = 0

    for order_time in order_times:
        # 选择用户
        email = random.choice(weighted_emails)

        # 生成订单号
        trade_no = f"TEST{order_time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

        # 每个订单1-3个商品
        num_items = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        selected_goods = random.sample(goods_pool, min(num_items, len(goods_pool)))

        # 计算订单总金额
        total_amount = Decimal("0")
        items_data = []
        for g in selected_goods:
            sku_id, name, p_price, jd_price, mk_price, brand, category = g
            price = p_price or jd_price or mk_price or Decimal("100")
            qty = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            total_amount += price * qty
            items_data.append((sku_id, qty))

        # 支付状态分布：70%已支付、20%待支付、10%已取消
        pay_rand = random.random()
        if pay_rand < 0.70:
            pay_status = "1"  # 已支付
            pay_time = order_time + timedelta(hours=random.randint(1, 48))
        elif pay_rand < 0.90:
            pay_status = "0"  # 待支付
            pay_time = None
        else:
            pay_status = "2"  # 已取消
            pay_time = None

        # 插入订单
        cursor.execute(
            "INSERT INTO `order` (trade_no, email, order_amount, address_id, pay_status, "
            "pay_time, is_delete, create_time, update_time) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (trade_no, email, total_amount, 1, pay_status, pay_time, 0, order_time, order_time)
        )
        order_count += 1

        # 插入订单商品
        for sku_id, qty in items_data:
            cursor.execute(
                "INSERT INTO order_goods (trade_no, sku_id, goods_num, create_time) "
                "VALUES (%s, %s, %s, %s)",
                (trade_no, sku_id, qty, order_time)
            )
            og_count += 1

        # 已支付订单30%概率生成评论
        if pay_status == "1" and random.random() < COMMENT_RATE:
            # 评论时间在订单支付后1-30天
            comment_time = pay_time + timedelta(days=random.randint(1, 30))
            if comment_time > now:
                comment_time = now - timedelta(days=random.randint(1, 10))

            for sku_id, _ in items_data:
                # 获取商品名称
                cursor.execute("SELECT name FROM goods WHERE sku_id = %s LIMIT 1", (sku_id,))
                g_name_row = cursor.fetchone()
                g_name = g_name_row[0] if g_name_row else "未知商品"

                # 评分分布：5分60%、4分25%、3分10%、2分3%、1分2%
                score_rand = random.random()
                if score_rand < 0.60:
                    score = Decimal("5.0")
                    sentiment = "positive"
                elif score_rand < 0.85:
                    score = Decimal("4.0")
                    sentiment = "positive"
                elif score_rand < 0.95:
                    score = Decimal("3.0")
                    sentiment = "neutral"
                elif score_rand < 0.98:
                    score = Decimal("2.0")
                    sentiment = "negative"
                else:
                    score = Decimal("1.0")
                    sentiment = "negative"

                # 评论内容模板
                positive_contents = [
                    "商品质量很好，物流也快，非常满意！",
                    "性价比很高，包装精美，推荐购买。",
                    "用了几天感觉不错，符合描述，好评。",
                    "第二次购买了，一如既往的好。",
                    "外观漂亮，功能齐全，家人都喜欢。"
                ]
                neutral_contents = [
                    "一般般，没有想象中好，但也不差。",
                    "质量还行，就是物流有点慢。",
                    "用着还可以，价格略贵。",
                    "基本满足需求，没什么惊喜。"
                ]
                negative_contents = [
                    "质量不行，用了一天就坏了，差评！",
                    "和描述不符，图片看起来好很多。",
                    "客服态度差，退货流程麻烦。",
                    "不值这个价，很失望。"
                ]

                if sentiment == "positive":
                    content = random.choice(positive_contents)
                elif sentiment == "neutral":
                    content = random.choice(neutral_contents)
                else:
                    content = random.choice(negative_contents)

                nickname = f"用户{random.randint(10000, 99999)}"

                cursor.execute(
                    "INSERT INTO comment (user_id, sku_id, reference_name, content, score, "
                    "nickname, is_verified, helpful_count, reply_count, sentiment, "
                    "sentiment_confidence, create_time) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (None, sku_id, g_name, content, score, nickname,
                     1 if random.random() < 0.6 else 0,
                     random.randint(0, 50),
                     random.randint(0, 5),
                     sentiment,
                     Decimal(str(round(random.uniform(0.7, 0.95), 2))),
                     comment_time)
                )
                comment_count += 1

        # 每100个订单提交一次
        if order_count % 100 == 0:
            conn.commit()
            print(f"  已生成 {order_count}/{len(order_times)} 个订单...")

    conn.commit()
    print(f"[订单] 生成 {order_count} 个订单")
    print(f"[订单商品] 生成 {og_count} 条订单商品记录")
    print(f"[评论] 生成 {comment_count} 条评论")
    return order_count


# ========== 清理测试数据 ==========
def clean_test_data(cursor, conn):
    """清除所有测试数据"""
    print("[清理] 开始清除测试数据...")

    # 先删除评论（关联测试订单的商品）
    cursor.execute(
        "DELETE FROM comment WHERE sku_id IN ("
        "  SELECT og.sku_id FROM order_goods og "
        "  JOIN `order` o ON og.trade_no = o.trade_no "
        "  WHERE o.trade_no LIKE 'TEST%')"
    )
    c1 = cursor.rowcount

    # 删除订单商品
    cursor.execute("DELETE FROM order_goods WHERE trade_no LIKE 'TEST%'")
    c2 = cursor.rowcount

    # 删除订单
    cursor.execute("DELETE FROM `order` WHERE trade_no LIKE 'TEST%'")
    c3 = cursor.rowcount

    # 删除测试用户
    cursor.execute("DELETE FROM user WHERE email LIKE %s", (f"{TEST_FLAG}%",))
    c4 = cursor.rowcount

    conn.commit()
    print(f"[清理] 删除评论 {c1} 条")
    print(f"[清理] 删除订单商品 {c2} 条")
    print(f"[清理] 删除订单 {c3} 个")
    print(f"[清理] 删除测试用户 {c4} 个")
    print("[清理] 完成！")


# ========== 主函数 ==========
def main():
    parser = argparse.ArgumentParser(description="数据分析Agent测试数据生成")
    parser.add_argument("--clean", action="store_true", help="清除测试数据")
    args = parser.parse_args()

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    if args.clean:
        clean_test_data(cursor, conn)
        conn.close()
        return

    print("=" * 60)
    print("  数据分析Agent - 测试数据生成")
    print("=" * 60)
    print()

    # 1. 获取商品池
    goods_pool = get_goods_pool(cursor)

    # 2. 生成用户
    user_count = generate_users(cursor, conn, NUM_USERS)

    # 3. 生成订单+订单商品+评论
    generate_orders(cursor, conn, goods_pool, user_count)

    # 4. 统计结果
    print()
    print("=" * 60)
    print("  数据生成完成！统计信息：")
    print("=" * 60)
    cursor.execute("SELECT COUNT(*) FROM user")
    print(f"  用户总数: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM `order`")
    print(f"  订单总数: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM `order` WHERE pay_status='1'")
    print(f"  已支付订单: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM `order` WHERE create_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
    print(f"  最近30天订单: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM `order` WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    print(f"  最近7天订单: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM comment")
    print(f"  评论总数: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM comment WHERE create_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
    print(f"  最近30天评论: {cursor.fetchone()[0]}")
    print()
    print("  现在可以测试以下场景：")
    print("  - 今日日报 / 本周周报")
    print("  - 最近30天销售额趋势")
    print("  - 热销商品TOP10")
    print("  - 用户分群分析（RFM）")
    print("  - 异常巡检")
    print("  - 商品评论分析")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
