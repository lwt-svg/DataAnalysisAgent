# 智能电商平台（Django + Vue3 + FastAPI + LangChain）

> 前后端分离的电商平台，集成基于大模型的电商智能助手

## 📋 项目概述

本项目是一个完整的电商解决方案，包含：
- **电商核心功能**：商品浏览、搜索、购物车、订单、支付
- **智能助手**：基于 LangChain + FastAPI 的 AI 购物助手，支持自然语言交互
- **技术栈**：Django REST Framework + Vue3 + Element Plus + FastAPI + LangChain

## 🏗️ 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Vue3 前端      │────▶│  Django 后端     │────▶│  FastAPI 智能体  │
│   (端口: 8080)  │     │  (端口: 8000)   │     │  (端口: 8001)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   MySQL 数据库   │
                        └─────────────────┘
```

### 服务说明

| 服务 | 技术 | 端口 | 职责 |
|------|------|------|------|
| 前端 | Vue3 + Element Plus | 8080 | 用户界面、交互 |
| 后端 | Django + DRF | 8000 | 业务逻辑、数据管理、JWT认证 |
| 智能体 | FastAPI + LangChain | 8001 | AI对话、意图识别、工具调用 |
| 数据库 | MySQL | 3306 | 数据持久化 |

## 📁 项目结构

```
django+vue3/
├── muxi_shop_web/              # Vue3 前端项目
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── Agent/          # 智能助手聊天页
│   │   │   ├── Cart/           # 购物车
│   │   │   ├── Goods/          # 商品详情/列表
│   │   │   ├── Order/          # 订单
│   │   │   └── Payment/        # 支付
│   │   ├── components/         # 公共组件
│   │   ├── network/            # API 请求封装
│   │   ├── router/             # 路由配置
│   │   └── store/              # Vuex 状态管理
│   ├── package.json
│   └── vue.config.js
│
├── muxi_shop_api/              # Django 后端项目
│   ├── apps/
│   │   ├── user/               # 用户管理
│   │   ├── goods/              # 商品管理
│   │   ├── cart/               # 购物车
│   │   ├── order/              # 订单
│   │   ├── pay/                # 支付(支付宝)
│   │   ├── comment/            # 评论
│   │   ├── address/            # 收货地址
│   │   └── agent/              # 智能助手代理
│   ├── muxi_shop_api/          # 项目配置
│   ├── static/                 # 静态文件
│   ├── manage.py
│   └── requirements.txt
│
└── docker-compose.yml          # Docker 部署配置 (可选)
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Redis (可选，用于缓存)

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd django+vue3
```

### 2. 配置数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE muxi_shop DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 启动 Django 后端

```bash
cd muxi_shop_api

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务
python manage.py runserver 8000
```

### 4. 启动 Vue3 前端

```bash
cd muxi_shop_web

# 安装依赖
npm install

# 开发模式启动
npm run serve

# 或构建生产版本
npm run build
```

### 5. 启动 FastAPI 智能体服务

> 智能体服务位于 `fastapi-langchain(latest)/ecommerce_agent/`

```bash
cd ../fastapi-langchain(latest)/ecommerce_agent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接和大模型 API Key

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 🔧 配置说明

### 后端配置 (muxi_shop_api/muxi_shop_api/settings.py)

```python
# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'muxi_shop',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# JWT 配置
JWT_SECRET_KEY = 'your-secret-key'
JWT_EXPIRATION_DELTA = timedelta(days=7)

# 智能体服务地址
AGENT_API_URL = 'http://localhost:8001'
```

### 前端配置 (muxi_shop_web/.env)

```
# 开发环境
VUE_APP_API_URL=http://localhost:8000
VUE_APP_AGENT_URL=http://localhost:8001
```

### 智能体配置 (fastapi-langchain/ecommerce_agent/.env)

```
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=muxi_shop

# 大模型 API (二选一)
DASHSCOPE_API_KEY=your-dashscope-key
# 或
OPENAI_API_KEY=your-openai-key

# JWT 密钥 (与 Django 保持一致)
JWT_SECRET_KEY=your-secret-key
```

## 🐳 Docker 部署

### 使用 Docker Compose 一键部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 开发模式（代码热更新）

`docker-compose.yml` 已配置 volumes 挂载，本地代码修改会自动同步到容器：

```yaml
services:
  backend:
    volumes:
      - ./muxi_shop_api:/app  # 代码挂载
  
  agent:
    volumes:
      - ../fastapi-langchain/ecommerce_agent:/app
```

修改代码后重启对应服务即可：

```bash
docker-compose restart backend
docker-compose restart agent
```

## 📱 功能特性

### 电商功能
- [x] 用户注册/登录/JWT认证
- [x] 商品分类浏览与搜索
- [x] 购物车管理
- [x] 订单创建与管理
- [x] 支付宝支付集成
- [x] 商品评论与评分
- [x] 收货地址管理

### 智能助手功能
- [x] 自然语言商品搜索
- [x] 智能商品推荐
- [x] 价格查询与比较
- [x] 评论摘要与情感分析
- [x] 购物车操作（添加/查看/删除）
- [x] 订单查询与状态跟踪
- [x] 多轮对话上下文保持
- [x] 会话历史保存与恢复

## 🔌 API 接口

### 电商接口 (Django)

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/user/register/` | POST | 用户注册 |
| `/api/user/login/` | POST | 用户登录 |
| `/api/goods/list/` | GET | 商品列表 |
| `/api/goods/detail/<id>/` | GET | 商品详情 |
| `/api/cart/` | GET/POST | 购物车操作 |
| `/api/order/` | GET/POST | 订单操作 |
| `/api/agent/chat/` | POST | 智能助手对话 |

### 智能体接口 (FastAPI)

| 接口 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/chat` | POST | 对话接口 |
| `/chat/sessions/list` | GET | 会话列表 |
| `/chat/sessions/save` | POST | 保存会话 |
| `/chat/sessions/load/{id}` | GET | 加载会话 |

## 🛠️ 技术亮点

### 1. 智能体架构
- **意图识别**：使用 LLM 识别用户意图
- **工具调用**：通过 LangChain Tools 调用电商 API
- **记忆管理**：支持多轮对话上下文保持
- **会话持久化**：Redis 存储会话历史

### 2. 前端技术
- Vue3 Composition API
- Element Plus 组件库
- Vuex 状态管理
- Axios 请求拦截
- 响应式布局设计

### 3. 后端技术
- Django REST Framework
- JWT 认证
- MySQL 数据库
- 支付宝 SDK 集成
- CORS 跨域处理

## 🐛 常见问题

### Q: 前端无法连接到后端？
A: 检查 `vue.config.js` 中的代理配置，确保与后端地址一致。

### Q: 智能体返回 "服务不可用"？
A: 确认 FastAPI 服务已启动，且 Django 中 `AGENT_API_URL` 配置正确。

### Q: 数据库连接失败？
A: 检查 MySQL 服务是否启动，以及数据库配置中的用户名密码是否正确。

### Q: JWT 认证失败？
A: 确保 Django 和 FastAPI 使用相同的 `JWT_SECRET_KEY`。

## 📄 许可证

MIT License

## 👨‍💻 作者

Your Name - [your-email@example.com](mailto:your-email@example.com)

## 🙏 致谢

- [Django](https://www.djangoproject.com/)
- [Vue.js](https://vuejs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://langchain.com/)
- [Element Plus](https://element-plus.org/)
