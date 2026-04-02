# 产品跟踪系统 (Product Tracking System)

一个基于 Django + Vue.js 的全栈产品跟踪系统，用于实时监控生产线上的货物状态。系统支持多产线、多工位、多通道的自动分流，提供扫码录入、实时数据追踪和完整的日志保留功能。

**[English](#english-version) | 中文**

---

## 功能特性

### 核心功能
- **🎯 实时货物状态追踪** - 通过 WebSocket 实现货物在线状态的实时更新，支持多生产线并行追踪
- **🔀 智能工位流转管理** - 支持多工位、多通道的自动判定和分流，可配置路由规则
- **📱 扫码录入支持** - 支持扫码枪/二维码扫描器录入，快速完成货物流转
- **📊 完整的日志系统** - 独立日志表，即使货物离线，7 天内仍可查询历史记录
- **🎨 现代化响应式界面** - 简洁明了的仪表盘，实时数据展示
- **🔧 RESTful API 设计** - 前后端完全分离，接口规范，易于集成

### 数据模型
- **Item（货物）** - 记录在线货物信息、位置、状态
- **ItemLog（货物日志）** - 独立记录所有货物历史，7 天自动清理
- **ScanRecord（扫码记录）** - 完整的扫码历史，关联到具体货物
- **RoutingRule（路由规则）** - 条码前缀匹配，自动分流通道判定
- **ProductionLine（产线）** - 多产线管理，支持产线级别的工位配置
- **Station（工位）** - 支持上线、分流、下线三种工位类型

---

## 技术栈

### 后端
- **Django 6.0+** - 企业级 Web 框架
- **Django REST Framework** - RESTful API 开发
- **Daphne** - ASGI 服务器，支持 WebSocket 实时通信
- **Django Channels** - WebSocket 组件（可选）
- **MySQL/SQLite** - 数据库支持

### 前端
- **Vue.js 3** - 现代前端框架
- **Vite** - 下一代构建工具
- **Axios** - HTTP 客户端库

### 依赖管理
| 包名 | 版本 | 用途 |
|-----|------|------|
| Django | 6.0.3 | Web 框架 |
| djangorestframework | 3.16.1 | API 开发 |
| django-cors-headers | 4.9.0 | CORS 跨域支持 |
| asgiref | 3.11.1 | ASGI 工具库 |
| mysqlclient | >=2.2.1 | MySQL 数据库驱动 |
| pandas | 最新 | 数据处理 |
| openpyxl | 最新 | Excel 文件处理 |

---

## 快速开始

### 前置要求
- **Python 3.8+** (推荐 3.10 或更高)
- **Node.js 18+** (推荐 LTS 版本)
- **MySQL 8.0+** 或 使用 SQLite (无需外部安装)
- **Git**
- **Git Bash** (Windows 用户推荐)

### 完整安装步骤

#### 1️⃣ 克隆项目

```bash
git clone https://github.com/Shirahagi/product-tracker.git
cd product-tracker
```

#### 2️⃣ 配置虚拟环境（后端）

**Windows:**
```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3️⃣ 数据库配置

**选项 A：使用 SQLite（推荐快速测试）**
```bash
# 无需额外配置，Django 默认使用 SQLite
# 执行数据库迁移
cd backend
python manage.py makemigrations
python manage.py migrate
```

**选项 B：使用 MySQL（生产环境推荐）**

1. 创建数据库和用户：
```sql
CREATE DATABASE product_tracker DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tracker_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON product_tracker.* TO 'tracker_user'@'localhost';
FLUSH PRIVILEGES;
```

2. 修改 `backend/backend/settings.py` (约第 82-92 行)：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'product_tracker',
        'USER': 'tracker_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

3. 执行数据库迁移：
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 3️⃣ᴮ 配置 Redis（可选但推荐）

Redis 用于缓存和实时数据传输，可显著提升系统性能。

**Windows:**
1. 下载 Redis：
   - 访问 [https://github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases)
   - 下载最新版本（如 `Redis-x64-3.2.100.msi` 或更新版本）
   - 双击安装，选择默认选项

2. 启动 Redis：
```bash
# Redis 作为服务已自动启动
# 或在命令行中手动启动
redis-server

# 验证连接
redis-cli ping
# 返回 PONG 表示成功
```

**macOS:**
```bash
# 使用 Homebrew 安装
brew install redis

# 启动 Redis
brew services start redis

# 或在终端手动启动
redis-server

# 验证连接
redis-cli ping
```

**Linux (Ubuntu/Debian):**
```bash
# 安装 Redis
sudo apt-get update
sudo apt-get install redis-server

# 启动 Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 验证连接
redis-cli ping
```

**Docker 方式（推荐）：**
```bash
# 拉取 Redis 镜像
docker pull redis:latest

# 运行 Redis 容器
docker run -d -p 6379:6379 --name redis redis:latest

# 验证连接
redis-cli ping
```

**修改 Django 设置以使用 Redis：**

编辑 `backend/backend/settings.py` 中的缓存配置（约第 130-140 行）：
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

#### 5️⃣ 启动后端服务

```bash
cd backend

# 使用 Daphne 运行（支持 WebSocket）
pip install daphne
daphne -b 0.0.0.0 -p 8000 backend.asgi:application

# 或使用标准 runserver（开发环境）
python manage.py runserver 0.0.0.0:8000
```

**后端访问地址：** `http://localhost:8000`

#### 6️⃣ 配置前端环境

```bash
cd ../frontend

# 安装 npm 依赖
npm install

# 启动开发服务器
npm run dev
```

**前端访问地址：** `http://localhost:5173`

#### 6️⃣ 初始化数据（可选）

```bash
cd ../backend

# 生成测试数据
python manage.py generate_test_data

# 创建超级用户（Django Admin）
python manage.py createsuperuser
```

**Django Admin 地址：** `http://localhost:8000/admin`

---

## 功能详解

### 1. 实时数据追踪

**功能描述：**
- 货物扫码后立即进入系统，显示在前端仪表盘
- 通过 WebSocket 实时推送位置、状态更新
- 支持按条码、名称、状态等多条件查询

**API 端点：**
```
GET  /api/items/                  # 获取所有在线货物
GET  /api/items/{id}/             # 获取指定货物详情
POST /api/items/                  # 新增货物
PUT  /api/items/{id}/             # 更新货物信息
DELETE /api/items/{id}/           # 货物下线（删除）
```

### 2. 工位流转与分流

**功能描述：**
- 系统根据条码前缀自动判定目标通道
- 支持自定义路由规则，灵活配置分流逻辑
- 工位类型：上线 → 分流 → 下线

**数据模型：**
- **ProductionLine（产线）** - 定义生产线名称和编码
- **Station（工位）** - 工位配置、类型、物理位置映射
- **RoutingRule（路由规则）** - 条码前缀 → 目标通道

**API 端点：**
```
GET  /api/routing-rules/          # 获取所有路由规则
POST /api/routing-rules/          # 添加新规则
PUT  /api/routing-rules/{id}/     # 修改规则
DELETE /api/routing-rules/{id}/   # 删除规则

GET  /api/stations/               # 获取所有工位
GET  /api/production-lines/       # 获取所有产线
```

**配置示例：**
```
条码前缀: A    →  目标通道: 通道1
条码前缀: B    →  目标通道: 通道2
条码前缀: C    →  目标通道: 通道3
```

### 3. 扫码录入

**支持方式：**
- ✅ 扫码枪输入（标准条码扫描设备）
- ✅ 手动输入（后备方案）
- ✅ API 集成（外部系统调用）

**流程：**
1. 货物扫码→条码识别
2. 系统查询路由规则→确定目标通道
3. 记录 `ScanRecord`→创建项目日志
4. 实时推送到前端→显示在仪表盘

**API 端点：**
```
POST /api/scan-records/           # 提交扫码记录
GET  /api/scan-records/?barcode=  # 查询扫码历史
```

### 4. 货物日志与历史

**功能描述：**
- 独立的 `ItemLog` 表，保存所有货物历史
- 即使货物下线（Item 删除），日志仍保留 7 天
- 自动清理过期日志，无需手动干预

**日志保留期：** 7 天（可配置）

**手动清理过期日志：**
```bash
# 清理超过 7 天的日志
python manage.py cleanup_old_logs

# 清理超过 14 天的日志
python manage.py cleanup_old_logs --days 14
```

**API 端点：**
```
GET  /api/item-logs/?barcode=     # 按条码查询日志
GET  /api/item-logs/              # 获取所有日志
```

### 5. 仪表盘与数据展示

**展示内容：**
- 📈 在线货物统计
- 📊 按通道分布统计
- 🕐 实时数据更新（WebSocket）
- 📋 完整的货物列表和搜索

**功能特性：**
- 字段过滤与排序
- 批量操作（下线等）
- 导出报表（推荐使用 pandas）

---

## 项目结构

```
product-tracker/
├── backend/                          # Django 后端
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── settings.py              # 项目设置（数据库、CORS 等）
│   │   ├── asgi.py                  # ASGI 配置（WebSocket）
│   │   ├── wsgi.py                  # WSGI 配置（WSGI 服务）
│   │   └── urls.py                  # 主 URL 路由
│   ├── tracker/                      # 核心应用逻辑
│   │   ├── models.py                # 数据模型（Item, ItemLog 等）
│   │   ├── views.py                 # API 视图
│   │   ├── serializers.py           # 序列化器
│   │   ├── urls.py                  # 应用 URL 路由
│   │   ├── consumers.py             # WebSocket 消费者
│   │   ├── routing.py               # WebSocket 路由
│   │   └── management/commands/     # 自定义管理命令
│   │       ├── cleanup_old_logs.py  # 清理日志
│   │       ├── generate_test_data.py# 生成测试数据
│   │       └── load_config.py       # 加载配置
│   ├── requirements.txt             # Python 依赖
│   ├── manage.py                    # Django 管理脚本
│   └── db.sqlite3                   # SQLite 数据库（开发用）
│
├── frontend/                         # Vue 前端
│   ├── src/
│   │   ├── App.vue                  # 主组件
│   │   ├── main.js                  # 入口点
│   │   ├── style.css                # 全局样式
│   │   ├── assets/                  # 静态资源
│   │   └── components/              # Vue 组件库
│   │       └── HelloWorld.vue
│   ├── public/                      # 公共静态文件
│   ├── package.json                 # npm 依赖
│   ├── vite.config.js              # Vite 配置
│   └── README.md
│
├── agents/                           # AI 代理和硬件模拟
│   ├── custom_opc_server.py         # OPC 服务器模拟（可选）
│   └── dynamic_opc_agent.py         # OPC 代理（可选）
│
├── tools/                            # 工具脚本
│   └── debug_node.py                # 调试工具
│
├── management/commands/              # 全局管理命令
│   └── clean_logs.py
│
├── 更新配置.bat                       # Windows 自动更新脚本
├── README.md                         # 项目说明（当前文件）
├── SYSTEM_IMPROVEMENTS.md           # 系统改进说明
└── .gitignore                        # Git 忽略文件配置
```

---

## 常见操作

### 创建超级用户
```bash
cd backend
python manage.py createsuperuser
```

### 生成测试数据
```bash
python manage.py generate_test_data
```

### 导出数据为 Excel
```bash
# 在 Django Shell 中
python manage.py shell
>>> from tracker.models import Item, ItemLog
>>> import pandas as pd
>>> 
>>> items = Item.objects.all()
>>> df = pd.DataFrame(items.values())
>>> df.to_excel('items.xlsx', index=False)
```

### 备份数据库

**SQLite：**
```bash
cp backend/db.sqlite3 backend/db.sqlite3.backup
```

**MySQL：**
```bash
mysqldump -u tracker_user -p product_tracker > backup.sql
```

---

## API 文档速览

### 货物管理
| 方法 | 端点 | 说明 |
|-----|------|------|
| GET | `/api/items/` | 获取所有在线货物 |
| POST | `/api/items/` | 添加新货物 |
| GET | `/api/items/{id}/` | 获取货物详情 |
| PUT | `/api/items/{id}/` | 更新货物信息 |
| DELETE | `/api/items/{id}/` | 货物下线 |

### 扫码与日志
| 方法 | 端点 | 说明 |
|-----|------|------|
| POST | `/api/scan-records/` | 提交扫码记录 |
| GET | `/api/scan-records/` | 查询扫码历史 |
| GET | `/api/item-logs/` | 获取货物日志 |
| GET | `/api/item-logs/?barcode=` | 按条码查询日志 |

### 配置管理
| 方法 | 端点 | 说明 |
|-----|------|------|
| GET | `/api/routing-rules/` | 获取所有路由规则 |
| POST | `/api/routing-rules/` | 添加新规则 |
| GET | `/api/production-lines/` | 获取所有产线 |
| GET | `/api/stations/` | 获取所有工位 |

---

## 故障排查

### 问题 1：数据库连接失败
**错误信息：** `django.db.utils.OperationalError`

**解决方案：**
- 检查 MySQL 是否运行： `mysql -u root -p`
- 检查 settings.py 中的数据库配置
- 确保数据库和用户已创建

### 问题 2：前端无法连接后端
**原因：** CORS 跨域问题

**解决方案：**
- 确保后端已启动
- 检查 `settings.py` 中的 `CORS_ALLOWED_ORIGINS` 包含前端地址

### 问题 3：WebSocket 连接失败
**原因：** 使用了 `runserver` 而不是 `daphne`

**解决方案：**
```bash
pip install daphne
daphne -b 0.0.0.0 -p 8000 backend.asgi:application
```

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

## 联系方式

- 📧 Email：support@example.com
- 🐛 Issues：请在 [GitHub Issues](https://github.com/Shirahagi/product-tracker/issues) 提交

---

## 更新日志

### v1.0.0 (2024-03-31)
- ✅ 初始版本发布
- ✅ 完成核心功能开发
- ✅ 数据模型优化（ItemLog 独立表）
- ✅ 完整的日志管理系统

---

## 相关资源

- [Django 官方文档](https://www.djangoproject.com/)
- [Vue.js 3 文档](https://vuejs.org/)
- [Django REST Framework 文档](https://www.django-rest-framework.org/)
- [Vite 官方文档](https://vitejs.dev/)
```

## 许可证

MIT License

## 作者
Shirahagi
