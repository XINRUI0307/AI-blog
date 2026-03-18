import os
import warnings
from datetime import datetime, timedelta
from flask import Flask, render_template
from sqlalchemy import event
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
from extensions import db, login_manager, migrate


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///database.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    app.config['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')

    if not app.config['ANTHROPIC_API_KEY']:
        warnings.warn(
            "ANTHROPIC_API_KEY is not set. AI features will not work.",
            RuntimeWarning,
            stacklevel=2,
        )

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.posts import posts_bp
    from routes.photos import photos_bp
    from routes.comments import comments_bp
    from routes.membership import membership_bp
    from routes.profile import profile_bp
    from routes.search import search_bp
    from routes.admin import admin_bp

    for bp in (auth_bp, posts_bp, photos_bp, comments_bp,
               membership_bp, profile_bp, search_bp, admin_bp):
        app.register_blueprint(bp)

    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

    @app.context_processor
    def inject_sidebar():
        from models import SidebarContent
        sidebar = SidebarContent.query.first()
        return dict(sidebar=sidebar)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    with app.app_context():
        _seed_admin()
        _purge_old_posts()

    return app


def _seed_admin():
    from models import User
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', email='admin@blog.com', role='admin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


def _purge_old_posts():
    from models import Post
    cutoff = datetime.utcnow() - timedelta(days=18 * 30)
    old = Post.query.filter(Post.created_at < cutoff).all()
    for post in old:
        db.session.delete(post)
    db.session.commit()


if __name__ == '__main__':
    load_dotenv()
    app = create_app()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'true').lower() == 'true')
