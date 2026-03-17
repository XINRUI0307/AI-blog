from flask import Blueprint, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Comment, Post

comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add(post_id):
    if current_user.role not in ('reader', 'contributor', 'admin'):
        abort(403)
    Post.query.get_or_404(post_id)
    body = request.form.get('body', '').strip()
    if not body:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('posts.detail', post_id=post_id))
    db.session.add(Comment(post_id=post_id, author_id=current_user.id, body=body))
    db.session.commit()
    flash('Comment added.', 'success')
    return redirect(url_for('posts.detail', post_id=post_id))


@comments_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user.role != 'admin':
        abort(403)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash('Comment removed.', 'success')
    return redirect(url_for('posts.detail', post_id=post_id))


@comments_bp.route('/comment/<int:comment_id>/report', methods=['POST'])
@login_required
def report(comment_id):
    if current_user.role not in ('reader', 'contributor'):
        abort(403)
    comment = Comment.query.get_or_404(comment_id)
    comment.is_reported = True
    db.session.commit()
    flash('Comment reported to admin.', 'info')
    return redirect(url_for('posts.detail', post_id=comment.post_id))
