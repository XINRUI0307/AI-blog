from flask import Blueprint, render_template, request
from models import Post, User

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
def results():
    q = request.args.get('q', '').strip()
    by = request.args.get('by', 'title')
    page = request.args.get('page', 1, type=int)
    pagination = None
    if q:
        if by == 'title':
            pagination = Post.query.filter(Post.title.ilike(f'%{q}%')).order_by(Post.created_at.desc()).paginate(page=page, per_page=12)
        elif by == 'location':
            pagination = Post.query.filter(Post.location.ilike(f'%{q}%')).order_by(Post.created_at.desc()).paginate(page=page, per_page=12)
        elif by == 'author':
            author_ids = [u.id for u in User.query.filter(User.username.ilike(f'%{q}%')).all()]
            if author_ids:
                pagination = Post.query.filter(Post.author_id.in_(author_ids)).order_by(Post.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('search/results.html', pagination=pagination, q=q, by=by)
