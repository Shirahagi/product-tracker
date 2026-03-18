# 产品跟踪系统 (Product Tracking System)

一个基于 Django + Vue.js 的全栈产品跟踪系统，用于实时监控生产线上的货物状态。

## 🚀 功能特性

- 📱 **实时货物状态追踪**：通过 WebSocket 实现实时更新。
- 🔄 **工位流转管理**：支持多工位、多通道的自动判定。
- 📊 **扫码录入支持**：支持扫码枪录入，快速流转。
- 🎨 **现代化响应式界面**：简洁明了的仪表盘。
- ⚡ **RESTful API 设计**：前后端分离，接口规范。
- 🤖 **硬件模拟代理**：提供 `hardware_agent.py` 模拟实际生产线扫码设备。

## 🛠️ 技术栈

### 后端
- **Django 6.0+** - Web 框架
- **Django REST Framework** - API 开发
- **Django Channels / Daphne** - WebSocket 实时通信
- **MySQL** - 关系型数据库

### 前端
- **Vue.js 3** - 用户界面框架
- **Vite** - 构建工具
- **Axios** - HTTP 客户端

### 硬件模拟
- **Python Requests** - 模拟设备扫码推送

## 📋 快速开始

### 环境要求
- Python 3.8+
- Node.js 18+
- MySQL 8.0+
- Git

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/Shirahagi/productline.git
   cd productline
   ```

2. **后端设置**
   ```bash
   cd backend
   # 创建虚拟环境
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # 安装依赖
   pip install -r requirements.txt
   
   # 数据库配置
   # 请确保本地 MySQL 已运行并创建了 product_tracker 数据库
   # 修改 backend/settings.py 中的 DATABASES 配置 (如有必要)
   
   # 数据库迁移
   python manage.py makemigrations
   python manage.py migrate
   # 启动后端服务器 (使用 daphne 运行以支持 WebSocket)
   python manage.py runserver
   ```

3. **前端设置**
   ```bash
   cd ../frontend
   # 安装依赖
   npm install
   # 启动开发服务器
   npm run dev
   ```

4. **硬件代理模拟 (可选)**
   ```bash
   # 在根目录下运行
   python hardware_agent.py
   ```

5. **访问应用**
   - 前端：[http://localhost:5173](http://localhost:5173)
   - 后端 API：[http://localhost:8000](http://localhost:8000)

## 🏗️ 项目结构

```
productline/
├── backend/                 # Django 后端
│   ├── backend/            # 项目配置 (settings.py, asgi.py)
│   ├── tracker/            # 核心逻辑应用
│   └── manage.py
├── frontend/               # Vue 前端
│   ├── src/
│   ├── public/
│   └── package.json
├── hardware_agent.py        # 硬件扫码模拟程序
├── .gitignore
└── README.md
```

## 📄 许可证

MIT License

## 👨‍💻 作者
Shirahagi
