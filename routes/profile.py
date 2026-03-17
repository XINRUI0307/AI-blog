import os
import uuid
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, abort)
from flask_login import login_required, current_user
from PIL import Image as PilImage
from extensions import db
from models import User, Message

profile_bp = Blueprint('profile', __name__)

AVATAR_ALLOWED = {'jpg', 'jpeg', 'png', 'webp'}


@profile_bp.route('/profile/<username>')
def view(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile/view.html', profile_user=user)


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio', '').strip()

        email = request.form.get('email', '').strip().lower()
        if email and email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already in use.', 'danger')
                return render_template('profile/edit.html')
            current_user.email = email

        avatar = request.files.get('avatar')
        if avatar and avatar.filename:
            ext = avatar.filename.rsplit('.', 1)[-1].lower()
            if ext not in AVATAR_ALLOWED:
                flash('Avatar must be jpg, jpeg, png, or webp.', 'danger')
                return render_template('profile/edit.html')
            try:
                img = PilImage.open(avatar)
                img.verify()
                avatar.seek(0)
            except Exception:
                flash('Invalid image file.', 'danger')
                return render_template('profile/edit.html')
            filename = f'{uuid.uuid4().hex}.{ext}'
            folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            if current_user.avatar_filename:
                old = os.path.join(folder, current_user.avatar_filename)
                if os.path.exists(old):
                    os.remove(old)
            avatar.save(os.path.join(folder, filename))
            current_user.avatar_filename = filename

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('profile.view', username=current_user.username))
    return render_template('profile/edit.html')


@profile_bp.route('/messages')
@login_required
def messages():
    inbox = (Message.query
             .filter_by(recipient_id=current_user.id)
             .order_by(Message.sent_at.desc())
             .all())
    for m in inbox:
        m.is_read = True
    db.session.commit()
    return render_template('profile/messages.html', messages=inbox)


@profile_bp.route('/messages/send/<int:recipient_id>', methods=['POST'])
@login_required
def send_message(recipient_id):
    if current_user.role != 'admin':
        abort(403)
    recipient = User.query.get_or_404(recipient_id)
    body = request.form.get('body', '').strip()
    if body:
        db.session.add(Message(sender_id=current_user.id,
                               recipient_id=recipient_id, body=body))
        db.session.commit()
        flash(f'Message sent to {recipient.username}.', 'success')
    return redirect(url_for('admin.users'))
