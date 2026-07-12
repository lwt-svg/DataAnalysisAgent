# 慕希商城 API - 智能电商平台后端

<div align="center">

![Django](https://img.shields.io/badge/Django-4.2.25-092E20?style=flat&logo=django)
![DRF](https://img.shields.io/badge/DRF-3.16.1-A30000?style=flat&logo=django)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat&logo=mysql)

**一个集成了电商智能体的前后端分离电商平台后端系统**

[功能特性](#-功能特性) • [技术栈](#-技术栈) • [快速开始](#-快速开始) • [API 文档](#-api-文档) • [项目结构](#-项目结构)

</div>

---

## 📖 项目简介

慕希商城是一个功能完整的 B2C 电商平台后端系统，采用前后端分离架构，集成了智能购物助手（Agent），能够为用户提供智能化的商品推荐、订单查询和购物咨询服务。

### 核心亮点

- 🤖 **智能客服 Agent** - 集成大语言模型，提供智能购物咨询和推荐
- 🛒 **完整电商流程** - 浏览、加购、下单、支付、评价全流程
- 💳 **支付宝支付** - 集成支付宝沙箱环境，支持真实支付流程
- 🔐 **JWT 认证** - 安全的身份认证和权限管理
- 📱 **RESTful API** - 规范的接口设计，便于前端对接

---

## ✨ 功能特性

### 用户模块
- ✅ 用户注册、登录、登出
- ✅ 个人信息管理（修改资料、头像）
- ✅ 密码修改（旧密码验证）
- ✅ JWT Token 身份认证

### 商品模块
- ✅ 商品分类浏览
- ✅ 商品详情查询
- ✅ 关键词搜索（支持排序）
- ✅ 商品推荐（发现好物）
- ✅ 商品图片展示

### 购物车模块
- ✅ 添加商品到购物车
- ✅ 修改商品数量
- ✅ 删除购物车商品
- ✅ 购物车商品列表
- ✅ 购物车商品数量统计

### 订单模块
- ✅ 创建订单（从购物车结算）
- ✅ 订单列表查询（按状态筛选）
- ✅ 订单详情查询
- ✅ 订单取消/删除
- ✅ 订单状态管理（待支付、已支付、已完成）

### 支付模块
- ✅ 支付宝沙箱支付集成
- ✅ 支付订单创建
- ✅ 异步回调处理
- ✅ 同步返回跳转
- ✅ 签名验证（RSA2）
- ✅ 模拟支付支持（开发环境）

### 地址模块
- ✅ 收货地址管理（增删改查）
- ✅ 默认地址设置
- ✅ 地址列表排序

### 评论模块
- ✅ 商品评论发布
- ✅ 评论列表查询（分页）
- ✅ 评论数量统计
- ✅ 评论删除

### Agent 智能助手
- ✅ 智能对话接口
- ✅ 商品推荐咨询
- ✅ 订单状态查询
- ✅ 购物问题解答
- ✅ 会话上下文管理

---

## 🛠️ 技术栈

### 后端框架
- **Django 4.2.25** - Web 框架
- **Django REST Framework 3.16.1** - REST API 框架
- **mysqlclient 2.2.7** - MySQL 数据库驱动
- **PyJWT 2.10.1** - JWT 认证
- **django-cors-headers 4.9.0** - 跨域支持
- **PyCryptodome 3.23.0** - 加密算法（支付宝签名）
- **Requests 2.32.5** - HTTP 请求库

### 数据库
- **MySQL 8.0** - 关系型数据库

### 前端（分离部署）
- **Vue 3** - 渐进式 JavaScript 框架
- **Axios** - HTTP 客户端
- **Pinia** - 状态管理
- **Element Plus** - UI 组件库

### Agent 服务（独立部署）
- **FastAPI** - 异步 API 框架
- **LangChain** - Agent 开发框架
- **Redis** - 会话存储

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- pip 包管理器

### 安装步骤

#### 1. 克隆项目
```bash
git clone <项目地址>
cd muxi_shop_api
```

#### 2. 创建虚拟环境（推荐）
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置数据库

创建 MySQL 数据库：
```sql
CREATE DATABASE muxi_shop DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `muxi_shop_api/settings.py` 中的数据库配置：
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "muxi_shop",
        "USER": "your_username",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
```

#### 5. 数据库迁移
```bash
# 如果已有数据库，需要反向生成模型
python manage.py inspectdb > apps/user/models.py
python manage.py inspectdb > apps/goods/models.py
# ... 其他应用

# 或者使用现有模型创建表
python manage.py makemigrations
python manage.py migrate
```

#### 6. 创建超级用户
```bash
python manage.py createsuperuser
```

#### 7. 启动开发服务器
```bash
python manage.py runserver
```

访问 `http://localhost:8000/admin/` 进入管理后台。

---

## 📚 API 文档

### 接口规范

**基础 URL:** `http://localhost:8000`

**统一响应格式:**
```json
{
  "status": 2000,
  "data": {}
}
```

**状态码说明:**
- `1000` 系列 - 菜单模块
- `2000` 系列 - 商品模块
- `3000` 系列 - 购物车模块
- `4000` 系列 - 用户模块
- `5000` 系列 - 评论模块
- `6000` 系列 - 订单模块

### 核心接口

#### 用户认证
```http
POST   /user/register/          # 用户注册
POST   /user/login/             # 用户登录
POST   /user/update/            # 更新用户信息
POST   /user/change_password/   # 修改密码
GET    /user/info/?email=xxx    # 获取用户信息
```

#### 商品管理
```http
GET    /goods/category/<category_id>/<page>/     # 商品分类列表
GET    /goods/detail/<sku_id>/                   # 商品详情
GET    /goods/find/                              # 发现好物
GET    /goods/search/<keyword>/<page>/<order>/   # 商品搜索
```

#### 购物车
```http
POST   /cart/              # 添加/更新/删除商品
GET    /cart/?email=xxx    # 获取购物车列表
GET    /cart/detail/       # 获取购物车详情（含商品信息）
POST   /cart/update_num/   # 更新商品数量
POST   /cart/count/        # 获取购物车商品总数
POST   /cart/delete/       # 批量删除商品
```

#### 订单管理
```http
POST   /order/                    # 创建订单
GET    /order/?pay_status=0       # 获取订单列表
GET    /order/detail/             # 获取订单详情
POST   /order/delete/             # 删除订单
POST   /order/update/             # 更新订单状态
```

#### 支付
```http
POST   /pay/create/               # 创建支付订单
POST   /pay/alipay/notify/        # 支付宝异步回调
GET    /pay/alipay/return/        # 支付宝同步返回
```

#### 地址管理
```http
POST   /address/                  # 新增地址
GET    /address/                  # 获取地址列表
PUT    /address/<pk>/             # 修改地址
DELETE /address/<pk>/             # 删除地址
POST   /address/update/           # 更新地址详情
```

#### 评论
```http
GET    /comment/<sku_id>/<page>/     # 商品评论列表
GET    /comment/count/<sku_id>/      # 评论数量
```

#### Agent 助手
```http
POST   /api/agent/chat/         # 与智能助手对话
GET    /api/agent/health/       # 检查 Agent 服务状态
```

### 请求示例

#### 用户登录
```bash
curl -X POST http://localhost:8000/user/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "123456"
  }'
```

#### 创建订单
```bash
curl -X POST http://localhost:8000/order/ \
  -H "Content-Type: application/json" \
  -H "Authorization: <your_token>" \
  -d '{
    "trade": {
      "order_amount": 99.00,
      "address_id": 1
    },
    "goods": [
      {
        "sku_id": "100000066136",
        "nums": 2
      }
    ]
  }'
```

---

## 📁 项目结构

```
muxi_shop_api/
├── apps/                          # 应用模块目录
│   ├── agent/                     # Agent 智能助手
│   │   ├── views.py               # Agent 对话接口
│   │   ├── urls.py                # 路由配置
│   │   └── models.py
│   ├── cart/                      # 购物车模块
│   │   ├── views.py               # 购物车视图
│   │   ├── serializers.py         # 序列化器
│   │   ├── models.py              # 数据模型
│   │   └── urls.py                # 路由配置
│   ├── comment/                   # 评论模块
│   ├── goods/                     # 商品模块
│   ├── order/                     # 订单模块
│   ├── pay/                       # 支付模块
│   │   ├── views.py               # 支付视图
│   │   ├── alipay.py              # 支付宝服务
│   │   └── urls.py
│   ├── user/                      # 用户模块
│   └── address/                   # 地址模块
├── muxi_shop_api/                 # 项目配置目录
│   ├── settings.py                # 主配置文件
│   ├── settings_dev.py            # 开发环境配置
│   ├── settings_prod.py           # 生产环境配置
│   ├── urls.py                    # 主路由配置
│   └── wsgi.py
├── utils/                         # 工具模块
│   ├── jwt_auth.py                # JWT 认证
│   ├── Password_Encoder.py        # 密码加密
│   └── ResponseMessage.py         # 统一响应封装
├── static/                        # 静态文件
│   └── product_images/            # 商品图片
├── manage.py                      # Django 管理脚本
├── requirements.txt               # 依赖列表
└── README.md                      # 项目文档
```

---

## 🔧 配置说明

### 关键配置项

#### 1. 数据库配置
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "muxi_shop",
        "USER": "admin",
        "PASSWORD": "123456",
        "HOST": "192.168.1.119",
    }
}
```

#### 2. JWT 认证配置
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["utils.jwt_auth.JwtHeaderAuthentication"]
}
```

#### 3. 支付宝配置
```python
ALIPAY_DEBUG = True  # 沙箱环境
APPID = "9021000158614658"
APP_NOTIFY_URL = "http://localhost:8000/pay/alipay/notify/"
RETURN_URL = "http://localhost:8000/pay/alipay/return/"
ENABLE_MOCK_PAYMENT = True  # 启用模拟支付
```

#### 4. Agent 服务配置
```python
AGENT_API_URL = "http://localhost:8000"  # FastAPI Agent 服务地址
```

#### 5. 跨域配置
```python
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
```

---

## 🧪 测试

### 运行测试
```bash
python manage.py test
```

### 使用 Postman 测试
导入 Postman 集合（如有），或使用以下配置：
- Base URL: `http://localhost:8000`
- Content-Type: `application/json`
- 认证接口：在 Header 中添加 `Authorization: <token>`

---

## 📊 数据库设计

### 核心数据表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `user` | 用户表 | email, password, name, mobile, gender |
| `goods` | 商品表 | sku_id, name, p_price, image, type_id |
| `shopping_cart` | 购物车表 | email, sku_id, nums, is_delete |
| `order` | 订单表 | trade_no, email, order_amount, pay_status |
| `order_goods` | 订单商品表 | trade_no, sku_id, goods_num |
| `user_address` | 地址表 | email, name, phone, address, default |
| `comment` | 评论表 | sku_id, email, content, rating |

---

## 🚀 部署指南

### 生产环境部署

#### 1. 使用 Gunicorn + Nginx
```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn muxi_shop_api.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

#### 2. Nginx 配置示例
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/static/;
    }
}
```

#### 3. 使用 Supervisor 管理进程
```ini
[program:muxi_shop]
command=/path/to/venv/bin/gunicorn muxi_shop_api.wsgi:application --bind 127.0.0.1:8000
directory=/path/to/muxi_shop_api
user=www-data
autostart=true
autorestart=true
```

---

## 🔒 安全建议

### 生产环境配置

1. **关闭 DEBUG**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your_domain.com']
   ```

2. **使用环境变量管理密钥**
   ```python
   SECRET_KEY = os.environ.get('SECRET_KEY')
   ```

3. **启用 HTTPS**
   - 配置 SSL 证书
   - 强制 HTTPS 重定向

4. **数据库权限控制**
   - 使用专用数据库用户
   - 限制权限范围

5. **定期备份数据**
   ```bash
   mysqldump -u admin -p muxi_shop > backup.sql
   ```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 开发计划

- [ ] 引入 Elasticsearch 优化商品搜索
- [ ] 添加商品库存管理
- [ ] 实现优惠券和促销活动
- [ ] 集成物流跟踪
- [ ] 添加数据分析和报表
- [ ] 实现多 Agent 协作
- [ ] 添加用户行为分析
- [ ] 优化 Agent 响应速度（流式输出）

---

## 📄 许可证

本项目仅供学习交流使用，禁止用于商业用途。

---

## 👨‍💻 作者

**个人项目** - 用于大模型应用工程师/Agent 工程师实习求职面试准备

---

## 📧 联系方式

如有问题，请通过以下方式联系：

- 项目 Issues: [提交 Issue](链接)
- 邮箱：your_email@example.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

</div>
