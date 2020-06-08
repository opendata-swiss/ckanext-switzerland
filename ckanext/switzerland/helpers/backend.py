"""
helpers belong in this file if they are only
used in backend templates
"""
import logging
from urlparse import urlparse
from ckan.common import session
from ckan.authz import auth_is_loggedin_user

log = logging.getLogger(__name__)

OGDCH_USER_VIEW_CHOICE = 'user_view_choice'
OGDCH_USER_VIEW_CHOICE_FRONTEND = 'frontend'
OGDCH_USER_VIEW_CHOICE_BACKEND = 'backend'


def ogdch_template_helper_get_active_class(active_url, section):
    """template helper: determines whether a link is an"""
    active_path = urlparse(active_url).path
    try:
        active_section = active_path.split('/')[1]
        if active_section == section:
            return 'active'
    except Exception:
        pass
    return ''


def ogdch_template_choice(template_frontend, template_backend):
    """decides whether to return a frontend
    or a backend template"""
    logged_in = auth_is_loggedin_user()
    if not logged_in:
        return template_frontend
    session_frontend = session \
        and OGDCH_USER_VIEW_CHOICE in session.keys() \
        and (session[OGDCH_USER_VIEW_CHOICE] == OGDCH_USER_VIEW_CHOICE_FRONTEND) # noqa
    if session_frontend:
        return template_frontend
    else:
        return template_backend
