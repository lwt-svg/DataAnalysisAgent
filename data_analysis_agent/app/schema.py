# 数据库Schema

import pymysql
from .config import DB_CONFIG

# 数据分析需要用到的表（去掉shopping_cart和user_address）
ANALYSIS_TABLES = [
    "user", "goods", "order", "order_goods", "comment"
]


def get_database_schema() -> str:
    """获取数据分析相关表的结构描述"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )
        cursor = conn.cursor()

        schema_lines = ["数据库表结构："]

        for table_name in ANALYSIS_TABLES:
            schema_lines.append(f"\n表 {table_name}：")
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            for col in columns:
                col_name, col_type, is_null, key, default, extra = col
                pk = " PRIMARY KEY" if key == "PRI" else ""
                schema_lines.append(f"  - {col_name} ({col_type}){pk}")

        # 补充表关系说明
        schema_lines.append("\n表关系：")
        schema_lines.append("  - order.email = user.email（用户订单）")
        schema_lines.append("  - order_goods.trade_no = order.trade_no（订单商品）")
        schema_lines.append("  - order_goods.sku_id = goods.sku_id（商品）")
        schema_lines.append("  - comment.sku_id = goods.sku_id（商品评论）")
        schema_lines.append("  - comment.email = user.email（用户评论）")
        schema_lines.append("\n关键字段说明：")
        schema_lines.append("  - order.pay_status: '0'=待支付, '1'=已支付, '2'=已取消/退货")
        schema_lines.append("  - order.is_delete: 0=正常, 1=已删除（软删除）")
        schema_lines.append("  - goods.main_brand: 品牌名（如'华为'/'小米'，'未知'表示未分类）")
        schema_lines.append("  - goods.main_category: 品类（如'手机'/'平板'/'流量卡'）")
        schema_lines.append("  - goods.jd_price: 售价（京东价）")
        schema_lines.append("  - goods.p_price: 采购价（成本价），可用于计算毛利")
        schema_lines.append("  - goods.mk_price: 市场价（参考价）")
        schema_lines.append("  - order_goods.goods_num: 购买数量")
        schema_lines.append("  - comment.score: 评分(1.0-5.0)")
        schema_lines.append("  - comment.sentiment: 情感分析('positive'/'neutral'/'negative')")

        # 业务概念字典（让LLM理解业务术语并知道如何用SQL计算）
        schema_lines.append("\n【业务概念字典 - SQL计算公式】")
        schema_lines.append("  - GMV(销售额) = SUM(order.order_amount) WHERE pay_status='1'")
        schema_lines.append("  - 客单价 = SUM(order.order_amount) WHERE pay_status='1' / COUNT(DISTINCT order.trade_no) WHERE pay_status='1'")
        schema_lines.append("  - 订单量 = COUNT(DISTINCT order.trade_no)")
        schema_lines.append("  - 退货率/取消率 = COUNT(*) WHERE pay_status='2' / COUNT(*) * 100")
        schema_lines.append("  - 支付率 = COUNT(*) WHERE pay_status='1' / COUNT(*) * 100")
        schema_lines.append("  - 毛利 = SUM((goods.jd_price - goods.p_price) * order_goods.goods_num)")
        schema_lines.append("    [需JOIN goods表: order_goods.sku_id = goods.sku_id]")
        schema_lines.append("  - 毛利率 = 毛利 / GMV * 100")
        schema_lines.append("  - 商品销量 = SUM(order_goods.goods_num)")
        schema_lines.append("  - 好评率 = COUNT(*) WHERE comment.score >= 4.0 / COUNT(comment) * 100")
        schema_lines.append("  - 复购率 = COUNT(DISTINCT email) WHERE 购买次数>=2 / COUNT(DISTINCT email) * 100")
        schema_lines.append("  - 转化率 ≈ 支付率 = pay_status='1'的订单 / 总订单 * 100（无浏览数据，用支付率近似）")

        return "\n".join(schema_lines)

    except Exception as e:
        return f"获取数据库结构时出错: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
