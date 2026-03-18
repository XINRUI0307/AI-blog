from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def contributor_required(f):
    return role_required('contributor', 'admin')(f)


def normalize_tags(raw: str) -> list[str]:
    """Parse comma-separated tag input into deduplicated, normalized list.
    Lowercase, stripped, spaces replaced with hyphens, max 50 chars each."""
    seen = set()
    result = []
    for token in raw.split(','):
        name = token.strip().lower().replace(' ', '-')[:50]
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def get_or_create_tag(name: str):
    """Return existing Tag or create new one. Caller must commit session."""
    from models import Tag
    tag = Tag.query.filter_by(name=name).first()
    if not tag:
        from extensions import db
        tag = Tag(name=name)
        db.session.add(tag)
    return tag
