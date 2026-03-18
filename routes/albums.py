from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Album, Post

albums_bp = Blueprint('albums', __name__)


@albums_bp.route('/albums')
def list_albums():
    page = request.args.get('page', 1, type=int)
    albums = Album.query.order_by(Album.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('albums/list.html', albums=albums)


@albums_bp.route('/album/<int:album_id>')
def detail(album_id):
    album = Album.query.get_or_404(album_id)
    return render_template('albums/detail.html', album=album)


@albums_bp.route('/album/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Album name is required.', 'danger')
            return render_template('albums/create.html')
        album = Album(
            user_id=current_user.id,
            name=name,
            description=request.form.get('description', '').strip()
        )
        db.session.add(album)
        db.session.commit()
        flash('Album created.', 'success')
        return redirect(url_for('albums.detail', album_id=album.id))
    return render_template('albums/create.html')


@albums_bp.route('/album/<int:album_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(album_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Album name is required.', 'danger')
            return render_template('albums/edit.html', album=album)
        album.name = name
        album.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Album updated.', 'success')
        return redirect(url_for('albums.detail', album_id=album.id))
    return render_template('albums/edit.html', album=album)


@albums_bp.route('/album/<int:album_id>/delete', methods=['POST'])
@login_required
def delete(album_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(album)
    db.session.commit()
    flash('Album deleted.', 'success')
    return redirect(url_for('albums.list_albums'))


@albums_bp.route('/album/<int:album_id>/add/<int:post_id>', methods=['POST'])
@login_required
def add_post(album_id, post_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    post = Post.query.get_or_404(post_id)
    if post not in album.posts:
        album.posts.append(post)
        db.session.commit()
        flash('Post added to album.', 'success')
    else:
        flash('Post is already in this album.', 'info')
    return redirect(request.referrer or url_for('albums.detail', album_id=album_id))


@albums_bp.route('/album/<int:album_id>/remove/<int:post_id>', methods=['POST'])
@login_required
def remove_post(album_id, post_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    post = Post.query.get_or_404(post_id)
    if post in album.posts:
        album.posts.remove(post)
        db.session.commit()
        flash('Post removed from album.', 'success')
    return redirect(request.referrer or url_for('albums.detail', album_id=album_id))
