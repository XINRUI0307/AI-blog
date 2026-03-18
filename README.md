# AI Blog Platform

一个功能完整的AI驱动的博客平台，提供文章发布、社区互动、会员管理和AI辅助功能。

## 功能特性

### 🚀 核心功能
- **用户管理**：用户注册、登录、资料编辑、头像上传
- **文章系统**：创建、编辑、发布、删除博客文章
- **评论系统**：文章评论、评论管理、评论举报
- **标签分类**：文章标签、标签浏览、热门标签
- **搜索功能**：全站文章搜索、分页显示
- **相册功能**：创建相册、管理照片、相册编辑/删除
- **会员系统**：会员申请、审核、认证管理
- **消息系统**：用户间私信功能
- **评分系统**：文章评分功能

### 🤖 AI功能
- 集成Anthropic API支持
- AI辅助内容生成（需配置ANTHROPIC_API_KEY）

### 👨‍💼 管理功能
- 管理员面板
- 用户审核管理
- 内容管理和审核

## 技术栈

- **后端框架**：Flask
- **数据库**：SQLite（支持WAL模式）
- **ORM**：SQLAlchemy + Alembic数据库迁移
- **用户认证**：Flask-Login
- **前端**：HTML/CSS/JavaScript
- **API集成**：Anthropic API

## 项目结构

```
blog-ai/
├── app.py                 # Flask应用入口
├── models.py              # 数据库模型
├── extensions.py          # Flask扩展配置
├── utils.py               # 工具函数
├── routes/                # 路由模块
│   ├── auth.py           # 认证相关
│   ├── posts.py          # 文章管理
│   ├── comments.py       # 评论管理
│   ├── tags.py           # 标签管理
│   ├── albums.py         # 相册管理
│   ├── photos.py         # 照片管理
│   ├── profile.py        # 用户资料
│   ├── search.py         # 搜索功能
│   ├── membership.py     # 会员管理
│   └── admin.py          # 管理功能
├── templates/             # HTML模板
├── static/                # 静态资源
├── migrations/            # 数据库迁移
└── instance/              # 实例配置
```

## 快速开始

### 前置要求
- Python 3.8+
- pip

### 安装与配置

1. **克隆项目**
```bash
git clone https://github.com/XINRUI0307/AI-blog.git
cd AI-blog
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
创建 `.env` 文件：
```
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=sqlite:///database.db
ANTHROPIC_API_KEY=your-api-key  # 可选
```

5. **初始化数据库**
```bash
flask db upgrade
```

6. **运行应用**
```bash
python app.py
# 或
flask run
```

访问 `http://localhost:5000`

## 数据库模型

主要模型包括：
- **User**：用户信息、认证、资料
- **Post**：博客文章
- **Comment**：文章评论
- **Tag**：标签分类
- **Photo**：照片
- **Album**：相册
- **Rating**：评分记录
- **Message**：用户消息
- **MembershipApplication**：会员申请

## API端点

### 认证
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `GET /auth/logout` - 用户登出

### 文章
- `GET /posts` - 获取文章列表
- `POST /posts` - 创建文章
- `GET /posts/<id>` - 获取文章详情
- `PUT /posts/<id>` - 编辑文章
- `DELETE /posts/<id>` - 删除文章

### 搜索
- `GET /search` - 搜索文章

### 用户资料
- `GET /profile/<username>` - 获取用户资料
- `POST /profile/update` - 更新资料

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- GitHub Issues：https://github.com/XINRUI0307/AI-blog/issues

---

*Built with ❤️ by AI Agent*
