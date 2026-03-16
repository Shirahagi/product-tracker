# 产品跟踪系统 (Product Tracking System)

一个基于Django + Vue.js的全栈产品跟踪系统，用于实时监控生产线上的货物状态。

## 🚀 功能特性

- 📱 实时货物状态追踪
- 🔄 工位流转管理
- 📊 扫码录入支持
- 🎨 现代化响应式界面
- ⚡ RESTful API设计

## 🛠️ 技术栈

### 后端
- **Django** - Web框架
- **Django REST Framework** - API开发
- **SQLite** - 数据库

### 前端
- **Vue.js 3** - 用户界面框架
- **Vite** - 构建工具
- **Axios** - HTTP客户端

## 📋 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- Git

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/YOUR_USERNAME/product-tracker.git
   cd product-tracker
   ```

2. **后端设置**
   ```bash
   # 创建虚拟环境
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # 安装依赖
   pip install -r requirements.txt
   # 数据库迁移
   python manage.py makemigrations
   python manage.py migrate
   # 启动后端服务器
   python manage.py runserver
   ```

3. **前端设置**
   ```bash
   cd frontend
   # 安装依赖
   npm install
   # 启动开发服务器
   npm run dev
   ```

4. **访问应用**
   - 前端：http://localhost:5173
   - 后端API：http://localhost:8000

## 📖 使用说明

1. 选择当前操作工位
2. 输入货物条码（支持扫码枪）
3. 点击提交或按回车
4. 查看实时更新的货物状态

## 🏗️ 项目结构

```
product-tracker/
├── backend/                 # Django后端
│   ├── backend/            # Django项目配置
│   ├── tracker/            # 应用模块
│   └── manage.py
├── frontend/               # Vue前端
│   ├── src/
│   ├── public/
│   └── package.json
├── venv/                   # Python虚拟环境
└── README.md
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

[Your Name] - [your.email@example.com]

---

⭐ 如果这个项目对你有帮助，请给它一个星标！