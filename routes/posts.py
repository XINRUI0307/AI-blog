from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Post, Rating
from utils import contributor_required

posts_bp = Blueprint('posts', __name__)


@posts_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('posts/index.html', posts=posts)


@posts_bp.route('/post/<int:post_id>')
def detail(post_id):
    post = Post.query.get_or_404(post_id)
    full_view = current_user.is_authenticated and current_user.role in ('reader', 'contributor', 'admin')
    user_rating = None
    if current_user.is_authenticated and current_user.role == 'reader':
        user_rating = Rating.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    return render_template('posts/detail.html', post=post, full_view=full_view, user_rating=user_rating)


@posts_bp.route('/post/create', methods=['GET', 'POST'])
@login_required
@contributor_required
def create():
    count = Post.query.filter_by(author_id=current_user.id).count()
    if count >= 10:
        flash('You have reached the 10-post limit.', 'warning')
        return redirect(url_for('posts.index'))
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        location = request.form.get('location', '').strip()
        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('posts/create.html')
        post = Post(title=title, description=description, location=location,
                    author_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Post created. You can now upload photos.', 'success')
        return redirect(url_for('photos.upload', post_id=post.id))
    remaining = 10 - Post.query.filter_by(author_id=current_user.id).count()
    return render_template('posts/create.html', remaining=remaining)


@posts_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    if request.method == 'POST':
        post.title = request.form['title'].strip()
        post.description = request.form['description'].strip()
        post.location = request.form.get('location', '').strip()
        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('posts.detail', post_id=post.id))
    return render_template('posts/edit.html', post=post)


@posts_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('posts.index'))


@posts_bp.route('/post/<int:post_id>/rate', methods=['POST'])
@login_required
def rate(post_id):
    if current_user.role != 'reader':
        abort(403)
    Post.query.get_or_404(post_id)
    stars = request.form.get('stars', type=int)
    if not stars or not (1 <= stars <= 5):
        flash('Invalid rating.', 'danger')
        return redirect(url_for('posts.detail', post_id=post_id))
    existing = Rating.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        existing.stars = stars
    else:
        db.session.add(Rating(post_id=post_id, user_id=current_user.id, stars=stars))
    db.session.commit()
    flash('Rating saved.', 'success')
    return redirect(url_for('posts.detail', post_id=post_id))
