# 电商数据分析Agent - 需求文档

## 一、产品定位

面向商家/运营的电商经营数据智能助手，用户用自然语言即可查询经营数据、分析趋势、发现异常、生成报告。与现有的C端购物助手形成B端+C端双Agent闭环。

## 二、目标用户

商家、运营人员、管理层（非技术背景，不会写SQL）

## 三、可用数据源（基于现有7张表）

### 3.1 用户表 (user)
| 字段 | 类型 | 说明 |
|------|------|------|
| email | varchar(255) | 用户ID（主键） |
| name | varchar(255) | 用户名 |
| mobile | varchar(255) | 手机号 |
| gender | varchar(255) | 性别 |
| birthday | datetime | 生日 |
| create_time | datetime | 注册时间 |

### 3.2 商品表 (goods)
| 字段 | 类型 | 说明 |
|------|------|------|
| sku_id | varchar(255) | 商品SKU |
| name | varchar(255) | 商品名 |
| p_price | decimal(10,2) | 售价 |
| jd_price | decimal(10,2) | 京东价 |
| mk_price | decimal(10,2) | 市场价 |
| main_brand | varchar | 品牌 |
| main_category | varchar | 品类 |
| shop_name | varchar(255) | 店铺名 |
| type_id | int | 分类ID |
| find | int | 是否推荐 |

### 3.3 订单表 (order)
| 字段 | 类型 | 说明 |
|------|------|------|
| trade_no | varchar(255) | 订单号 |
| email | varchar(255) | 用户邮箱 |
| order_amount | decimal(10,2) | 订单金额 |
| address_id | int | 地址ID |
| pay_status | varchar(155) | 支付状态（0=待支付, 1=已支付） |
| pay_time | datetime | 支付时间 |
| ali_trade_no | varchar(255) | 支付宝交易号 |
| is_delete | int | 是否删除 |
| create_time | datetime | 创建时间 |

### 3.4 订单商品表 (order_goods)
| 字段 | 类型 | 说明 |
|------|------|------|
| trade_no | varchar(255) | 订单号 |
| sku_id | varchar(255) | 商品SKU |
| goods_num | int | 商品数量 |
| create_time | datetime | 创建时间 |

### 3.5 评论表 (comment)
| 字段 | 类型 | 说明 |
|------|------|------|
| sku_id | varchar(255) | 商品SKU |
| email | varchar(255) | 用户邮箱 |
| content | text | 评论内容 |
| score | decimal | 评分 |
| reference_name | varchar | 商品名称 |
| nickname | varchar | 昵称 |
| create_time | datetime | 评论时间 |

### 3.6 购物车表 (shopping_cart)
| 字段 | 类型 | 说明 |
|------|------|------|
| sku_id | varchar(255) | 商品SKU |
| nums | int | 数量 |
| is_delete | int | 是否删除 |
| email | varchar(255) | 用户邮箱 |
| create_time | datetime | 创建时间 |

### 3.7 地址表 (user_address)
| 字段 | 类型 | 说明 |
|------|------|------|
| email | varchar | 用户邮箱 |
| name | varchar | 收件人 |
| phone | varchar | 电话 |
| address | varchar | 地址 |
| default | int | 是否默认 |

---

## 四、功能需求（8大模块）

### 4.1 销售数据查询
| 功能 | 用户示例 | 数据来源 |
|------|---------|---------|
| 总GMV | "今天/本周/本月卖了多少钱" | order表 SUM(order_amount) WHERE pay_status=1 |
| 订单量 | "今天有多少订单" | order表 COUNT(*) |
| 客单价 | "平均客单价多少" | SUM(order_amount)/COUNT(*) |
| 支付转化率 | "下单后支付的比例" | 已支付数/总订单数 |

### 4.2 销售趋势分析
| 功能 | 用户示例 | 数据来源 |
|------|---------|---------|
| 日销售趋势 | "最近7天/30天的销售趋势" | order表按日聚合GMV和订单量 |
| 环比增长 | "这周比上周增长了多少" | 本周GMV/上周GMV - 1 |
| 同比增长 | "今年和去年同期比" | 同上，跨年对比 |
| 品类趋势 | "手机品类最近趋势" | 关联goods表按品类过滤后聚合 |

### 4.3 商品排行榜
| 功能 | 用户示例 | 数据来源 |
|------|---------|---------|
| 销量排行 | "卖得最好的10个商品" | order_goods表 GROUP BY sku_id ORDER BY SUM(goods_num) |
| 销售额排行 | "收入最高的商品" | 关联order+order_goods+goods按金额排序 |
| 品类排行 | "哪个品类卖得最好" | 关联goods表按main_category聚合 |
| 品牌排行 | "哪个品牌最受欢迎" | 关联goods表按main_brand聚合 |
| 滞销商品 | "哪些商品没人买" | goods表 LEFT JOIN order_goods，找不到订单记录的 |

### 4.4 用户分析
| 功能 | 用户示例 | 数据来源 |
|------|---------|---------|
| 用户总量 | "平台有多少用户" | user表 COUNT(*) |
| 注册趋势 | "最近一周新增用户" | user表按create_time聚合 |
| 性别分布 | "男女用户比例" | user表 GROUP BY gender |
| 消费排行 | "消费最多的用户" | order表 GROUP BY email ORDER BY SUM(order_amount) |
| RFM分群 | "我的核心用户/沉睡用户" | R(最近购买)/F(购买频率)/M(消费金额)三维度分群 |

### 4.5 订单分析
| 功能 | 用户示例 | 数据来源 |
|------|---------|---------|
| 订单状态分布 | "多少订单待支付/已支付" | order表 GROUP BY pay_status |
| 退款率 | "退款率怎么样" | is_delete=1的订单占比 |
| 订单金额分布 | "订单大多多少钱" | order表按金额区间分组 |
| 平均支付时间 | "用户多久完成支付" | pay_time - create_time的平均值 |

### 4.6 评论分析
| 功能 | 用户示例 | 数据来源 |
|------|---------|---------|
| 平均评分 | "商品平均评分" | comment表 AVG(score) |
| 评分分布 | "各评分段占比" | comment表 GROUP BY FLOOR(score) |
| 差评商品 | "哪些商品差评多" | comment表 WHERE score<=2 GROUP BY sku_id |
| 评论量趋势 | "评论数量趋势" | comment表按日聚合 |

### 4.7 异常检测
| 功能 | 用户示例 | 算法 |
|------|---------|------|
| 订单量异常 | "今天订单量正常吗" | Z-Score：当日订单量与7日均值对比，|Z|>2为异常 |
| GMV异常 | "今天收入有没有异常" | 同上，对GMV做检测 |
| 评分骤降 | "最近评分有没有下降" | 近3天均分 vs 30天均分，下降>0.5为异常 |

### 4.8 报告生成
| 功能 | 用户示例 | 输出 |
|------|---------|------|
| 日报 | "帮我生成今日经营日报" | Markdown格式：GMV+订单量+TOP3商品+异常项 |
| 周报 | "这周的经营报告" | Markdown格式：趋势+排行+用户+异常+建议 |
| 对比报告 | "这周和上周对比" | 环比数据+变化率+亮点/问题 |

---

## 五、意图设计（8种）

| 意图 | 关键词 | 优先级 |
|------|--------|--------|
| sales_query | 多少钱/GMV/销售额/收入/客单价 | 最高 |
| trend_analysis | 趋势/环比/同比/增长/变化 | 高 |
| product_ranking | 排行/排行/卖得最好/滞销/销量 | 高 |
| user_analysis | 用户/客户/RFM/核心用户/性别 | 高 |
| order_analysis | 订单/支付/退款/待支付 | 中 |
| comment_analysis | 评分/评论/好评/差评 | 中 |
| anomaly_check | 异常/正常吗/有没有问题 | 中 |
| report_generation | 报告/日报/周报/月报 | 低（最复杂） |
| general | 其他 | 兜底 |

---

## 六、前端方案

### 方案A：集成到现有电商系统（推荐）

在现有Vue3电商前端中新增一个"数据助手"页面，与"购物助手"并列。

```
现有前端导航：
  首页 | 分类 | 购物车 | 我的 | 购物助手
  
改后：
  首页 | 分类 | 购物车 | 我的 | 购物助手 | 数据助手（仅管理员可见）
```

**优点**：
- 不用新建前端项目，复用现有布局、路由、状态管理
- 用户身份直接复用JWT token，购物助手和数据助手共享登录态
- 面试时展示"一个系统两个Agent"的完整架构

**缺点**：
- 需要在现有Vue3项目中加页面

### 方案B：独立前端

单独新建一个Vue3项目，只做数据分析助手。

**优点**：独立部署，不影响现有前端
**缺点**：多一个项目维护，登录态需要跨域处理，面试时显得割裂

### 推荐：方案A

数据分析助手的聊天界面跟购物助手几乎一样（消息列表+输入框），只是后端Agent不同（8001 vs 8002），前端只需加一个路由，把API请求发到不同端口。

---

## 七、非功能需求

| 项目 | 要求 |
|------|------|
| 响应时间 | 简单查询<3s，报告生成<10s |
| SQL安全 | 只允许SELECT，禁止INSERT/UPDATE/DELETE，必须有LIMIT |
| 大数据量保护 | 所有聚合查询必须有时间范围限制（默认最近30天），禁止全表扫描 |
| 并发 | 支持5个商家同时使用 |
| 可观测性 | 复用LangFuse，与购物助手在同一个项目下 |
