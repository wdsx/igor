from functools import wraps
from flask import request, abort
from wds.landlord import landlord


def secure(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = landlord.Tenant()
        tenant.load_properties()
        if request.headers.get('X-Igor-Token') and request.headers.get('X-Igor-Token') == tenant.get_property('token'):
            return f(*args, **kwargs)
        return abort(401)
    return decorated_function