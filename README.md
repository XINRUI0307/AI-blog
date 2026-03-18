# AI Blog Platform

A comprehensive AI-powered blogging platform featuring article publishing, community interaction, membership management, and AI-assisted functionality.

## Features

### 🚀 Core Features
- **User Management**: User registration, login, profile editing, avatar upload
- **Article System**: Create, edit, publish, and delete blog articles
- **Comment System**: Article comments, comment management, comment reporting
- **Tag Classification**: Article tags, tag browsing, popular tags
- **Search Functionality**: Full-site article search with pagination
- **Album Features**: Create albums, manage photos, album editing/deletion
- **Membership System**: Membership applications, approval, certification management
- **Messaging System**: Private messaging between users
- **Rating System**: Article rating functionality

### 🤖 AI Features
- Anthropic API integration
- AI-assisted content generation (requires ANTHROPIC_API_KEY configuration)

### 👨‍💼 Admin Features
- Admin dashboard
- User approval and management
- Content management and moderation

## Tech Stack

- **Backend Framework**: Flask
- **Database**: SQLite (with WAL mode support)
- **ORM**: SQLAlchemy + Alembic database migrations
- **Authentication**: Flask-Login
- **Frontend**: HTML/CSS/JavaScript
- **API Integration**: Anthropic API

## Project Structure

```
blog-ai/
├── app.py                 # Flask application entry point
├── models.py              # Database models
├── extensions.py          # Flask extensions configuration
├── utils.py               # Utility functions
├── routes/                # Route modules
│   ├── auth.py           # Authentication routes
│   ├── posts.py          # Article management
│   ├── comments.py       # Comment management
│   ├── tags.py           # Tag management
│   ├── albums.py         # Album management
│   ├── photos.py         # Photo management
│   ├── profile.py        # User profile
│   ├── search.py         # Search functionality
│   ├── membership.py     # Membership management
│   └── admin.py          # Admin functionality
├── templates/             # HTML templates
├── static/                # Static assets
├── migrations/            # Database migrations
└── instance/              # Instance configuration
```

## Quick Start

### Requirements
- Python 3.8+
- pip

### Installation & Setup

1. **Clone the repository**
```bash
git clone https://github.com/XINRUI0307/AI-blog.git
cd AI-blog
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file:
```
SECRET_KEY=your-secret-key
SQLALCHEMY_DATABASE_URI=sqlite:///database.db
ANTHROPIC_API_KEY=your-api-key  # Optional
```

5. **Initialize database**
```bash
flask db upgrade
```

6. **Run the application**
```bash
python app.py
# or
flask run
```

Visit `http://localhost:5000`

## Database Models

Main models include:
- **User**: User information, authentication, profile
- **Post**: Blog articles
- **Comment**: Article comments
- **Tag**: Tag classification
- **Photo**: Photos
- **Album**: Albums
- **Rating**: Rating records
- **Message**: User messages
- **MembershipApplication**: Membership applications

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Articles
- `GET /posts` - Get article list
- `POST /posts` - Create article
- `GET /posts/<id>` - Get article details
- `PUT /posts/<id>` - Edit article
- `DELETE /posts/<id>` - Delete article

### Search
- `GET /search` - Search articles

### User Profile
- `GET /profile/<username>` - Get user profile
- `POST /profile/update` - Update profile

## License

MIT License

## Contributing

We welcome Issue submissions and Pull Requests!

## Contact

- GitHub Issues: https://github.com/XINRUI0307/AI-blog/issues

---

*Built with ❤️ by AI Agent*
