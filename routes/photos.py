import os
import uuid
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, send_from_directory, abort)
from flask_login import login_required, current_user
from PIL import Image as PilImage
from extensions import db
from models import Post, Image

photos_bp = Blueprint('photos', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_WIDTH, MAX_HEIGHT = 1200, 800


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@photos_bp.route('/post/<int:post_id>/upload', methods=['GET', 'POST'])
@login_required
def upload(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    if request.method == 'POST':
        files = request.files.getlist('photos')
        saved = 0
        for f in files:
            if not f or not f.filename:
                continue
            if not _allowed(f.filename):
                flash(f'Skipped {f.filename}: unsupported file type.', 'warning')
                continue
            f.seek(0, 2)
            size = f.tell()
            f.seek(0)
            if size > 10 * 1024 * 1024:
                flash(f'{f.filename} exceeds the 10 MB limit.', 'danger')
                continue
            try:
                img = PilImage.open(f)
                if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
                    flash(f'{f.filename}: resolution {img.width}x{img.height} exceeds 1200x800.', 'danger')
                    continue
            except Exception:
                flash(f'{f.filename} is not a valid image.', 'danger')
                continue
            f.seek(0)
            ext = f.filename.rsplit('.', 1)[1].lower()
            filename = f'{uuid.uuid4().hex}.{ext}'
            folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', str(post_id))
            os.makedirs(folder, exist_ok=True)
            f.save(os.path.join(folder, filename))
            db.session.add(Image(post_id=post_id, filename=filename))
            saved += 1
        db.session.commit()
        if saved:
            flash(f'{saved} photo(s) uploaded.', 'success')
        return redirect(url_for('posts.detail', post_id=post_id))
    return render_template('photos/upload.html', post=post)


@photos_bp.route('/uploads/posts/<int:post_id>/<filename>')
def serve_post_photo(post_id, filename):
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', str(post_id))
    return send_from_directory(folder, filename)


@photos_bp.route('/uploads/avatars/<filename>')
def serve_avatar(filename):
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
    return send_from_directory(folder, filename)


@photos_bp.route('/photo/<int:image_id>/download')
def download(image_id):
    image = Image.query.get_or_404(image_id)
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', str(image.post_id))
    return send_from_directory(folder, image.filename, as_attachment=True)


@photos_bp.route('/photo/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_photo(image_id):
    image = Image.query.get_or_404(image_id)
    post = Post.query.get(image.post_id)
    if post.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts',
                            str(image.post_id), image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(image)
    db.session.commit()
    flash('Photo deleted.', 'success')
    return redirect(url_for('posts.detail', post_id=image.post_id))
