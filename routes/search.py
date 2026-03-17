from flask import Blueprint, render_template, request
from models import Post, User

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
def results():
    q = request.args.get('q', '').strip()
    by = request.args.get('by', 'title')
    posts = []
    if q:
        if by == 'title':
            posts = Post.query.filter(Post.title.ilike(f'%{q}%')).all()
        elif by == 'location':
            posts = Post.query.filter(Post.location.ilike(f'%{q}%')).all()
        elif by == 'author':
            author_ids = [u.id for u in User.query.filter(User.username.ilike(f'%{q}%')).all()]
            posts = Post.query.filter(Post.author_id.in_(author_ids)).all() if author_ids else []
    return render_template('search/results.html', posts=posts, q=q, by=by)
