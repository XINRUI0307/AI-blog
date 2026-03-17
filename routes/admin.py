from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user
from extensions import db
from models import User, Post, Comment, MembershipApplication, SidebarContent

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
def check_admin():
    if not current_user.is_authenticated or current_user.role != 'admin':
        abort(403)


@admin_bp.route('/')
def dashboard():
    pending_count = MembershipApplication.query.filter_by(status='pending').count()
    reported_count = Comment.query.filter_by(is_reported=True).count()
    user_count = User.query.count()
    post_count = Post.query.count()
    sidebar = SidebarContent.query.first()
    return render_template('admin/dashboard.html',
                           pending_count=pending_count,
                           reported_count=reported_count,
                           user_count=user_count,
                           post_count=post_count,
                           sidebar=sidebar)


@admin_bp.route('/applications')
def applications():
    apps = (MembershipApplication.query
            .order_by(MembershipApplication.applied_at.desc())
            .all())
    return render_template('admin/applications.html', applications=apps)


@admin_bp.route('/applications/<int:app_id>/approve', methods=['POST'])
def approve_application(app_id):
    app = MembershipApplication.query.get_or_404(app_id)
    app.status = 'approved'
    app.reviewed_at = datetime.utcnow()
    user = User.query.get(app.user_id)
    user.role = app.requested_role
    user.is_active = True
    db.session.commit()
    flash(f'{user.username} approved as {user.role}.', 'success')
    return redirect(url_for('admin.applications'))


@admin_bp.route('/applications/<int:app_id>/reject', methods=['POST'])
def reject_application(app_id):
    app = MembershipApplication.query.get_or_404(app_id)
    app.status = 'rejected'
    app.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash('Application rejected.', 'info')
    return redirect(url_for('admin.applications'))


@admin_bp.route('/users')
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot deactivate admin accounts.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    state = 'activated' if user.is_active else 'deactivated'
    flash(f'{user.username} {state}.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/reported-comments')
def reported_comments():
    comments = (Comment.query
                .filter_by(is_reported=True)
                .order_by(Comment.created_at.desc())
                .all())
    return render_template('admin/reported_comments.html', comments=comments)


@admin_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'success')
    return redirect(url_for('admin.reported_comments'))


@admin_bp.route('/sidebar', methods=['POST'])
def update_sidebar():
    content = request.form.get('content', '')
    sidebar = SidebarContent.query.first()
    if sidebar:
        sidebar.content = content
    else:
        db.session.add(SidebarContent(content=content))
    db.session.commit()
    flash('Sidebar updated.', 'success')
    return redirect(url_for('admin.dashboard'))
