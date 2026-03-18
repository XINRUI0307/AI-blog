from flask import Blueprint, render_template
from models import Tag

tags_bp = Blueprint('tags', __name__)


@tags_bp.route('/tag/<tag_name>')
def browse(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    return render_template('tags/browse.html', tag=tag, posts=tag.posts)
