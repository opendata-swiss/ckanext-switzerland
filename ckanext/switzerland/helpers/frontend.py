"""
helpers belong in this file if they
are used in frontend templates
"""
import ckan.plugins.toolkit as tk
import ckan.logic as logic
from ckan import model as model
import requests
import json
from ckan.common import _
from babel import numbers

from ckan.lib.helpers import lang, url_for, localised_number
import ckan.lib.i18n as i18n
import unicodedata
import ckanext.switzerland.helpers.localize as loc
import ckanext.switzerland.helpers.terms_of_use as terms

import logging
log = logging.getLogger(__name__)

# these bookmarks can be used in the wordpress page
# for the terms of use
mapping_terms_of_use_to_pagemark = {
    terms.TERMS_OF_USE_OPEN: '#terms_open',
    terms.TERMS_OF_USE_BY: '#terms_by',
    terms.TERMS_OF_USE_ASK: '#terms_ask',
    terms.TERMS_OF_USE_BY_ASK: '#terms_by_ask',
}


def get_dataset_count():
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}

    packages = tk.get_action('package_search')(
        req_context,
        {'fq': '+dataset_type:dataset'}
    )
    return packages['count']


def get_group_count():
    '''
    Return the number of groups
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    groups = tk.get_action('group_list')(req_context, {})
    return len(groups)


def get_org_count():
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    orgs = tk.get_action('organization_list')(req_context, {})
    return len(orgs)


def get_app_count():
    result = _call_wp_api('app_statistics')
    if result is not None:
        return result['data']['app_count']
    return 0


def _call_wp_api(action):
    api_url = tk.config.get('ckanext.switzerland.wp_ajax_url', None)
    try:
        """
        this call does not verify the SSL cert, because it is missing on
        the deployed server.
        TODO: re-enable verification
        """
        r = requests.post(api_url, data={'action': action}, verify=False)
        return r.json()
    except:
        return None


def get_localized_org(org_id=None, include_datasets=False):
    if not org_id or org_id is None:
        return {}
    try:
        return logic.get_action('organization_show')(
            {'for_view': True},
            {'id': org_id, 'include_datasets': include_datasets}
        )
    except (logic.NotFound, logic.ValidationError,
            logic.NotAuthorized, AttributeError):
        return {}


def localize_json_title(facet_item):
    # json.loads tries to convert numbers in Strings to integers. At this point
    # we only need to deal with Strings, so we let them be Strings.
    try:
        int(facet_item['display_name'])
        return facet_item['display_name']
    except (ValueError, TypeError):
        pass
    try:
        lang_dict = json.loads(facet_item['display_name'])
        return loc.get_localized_value_from_dict(
            lang_dict,
            lang_code=lang(),
            default=facet_item['display_name']
        )
    except:
        return facet_item['display_name']


def get_frequency_name(identifier):
    frequencies = {
      'http://purl.org/cld/freq/completelyIrregular': _('Irregular'),  # noqa
      'http://purl.org/cld/freq/continuous': _('Continuous'),  # noqa
      'http://purl.org/cld/freq/daily': _('Daily'),  # noqa
      'http://purl.org/cld/freq/threeTimesAWeek': _('Three times a week'),  # noqa
      'http://purl.org/cld/freq/semiweekly': _('Semi weekly'),  # noqa
      'http://purl.org/cld/freq/weekly': _('Weekly'),  # noqa
      'http://purl.org/cld/freq/threeTimesAMonth': _('Three times a month'),  # noqa
      'http://purl.org/cld/freq/biweekly': _('Biweekly'),  # noqa
      'http://purl.org/cld/freq/semimonthly': _('Semimonthly'),  # noqa
      'http://purl.org/cld/freq/monthly': _('Monthly'),  # noqa
      'http://purl.org/cld/freq/bimonthly': _('Bimonthly'),  # noqa
      'http://purl.org/cld/freq/quarterly': _('Quarterly'),  # noqa
      'http://purl.org/cld/freq/threeTimesAYear': _('Three times a year'),  # noqa
      'http://purl.org/cld/freq/semiannual': _('Semi Annual'),  # noqa
      'http://purl.org/cld/freq/annual': _('Annual'),  # noqa
      'http://purl.org/cld/freq/biennial': _('Biennial'),  # noqa
      'http://purl.org/cld/freq/triennial': _('Triennial'),  # noqa
    }
    try:
        return frequencies[identifier]
    except KeyError:
        return identifier


def get_political_level(political_level):
    political_levels = {
        'confederation': _('Confederation'),
        'canton': _('Canton'),
        'commune': _('Commune'),
        'other': _('Other')
    }
    return political_levels.get(political_level, political_level)


def get_terms_of_use_icon(terms_of_use):
    term_to_image_mapping = {
        terms.TERMS_OF_USE_OPEN: {  # noqa
            'title': _('Open use'),
            'icon': 'terms_open',
        },
        terms.TERMS_OF_USE_BY: {  # noqa
            'title': _('Open use. Must provide the source.'),
            'icon': 'terms_by',
        },
        terms.TERMS_OF_USE_ASK: {  # noqa
            'title': _('Open use. Use for commercial purposes requires permission of the data owner.'),  # noqa
            'icon': 'terms_ask',
        },
        terms.TERMS_OF_USE_BY_ASK: {  # noqa
            'title': _('Open use. Must provide the source. Use for commercial purposes requires permission of the data owner.'),  # noqa
            'icon': 'terms_by-ask',
        },
        terms.TERMS_OF_USE_CLOSED: {
            'title': _('Closed data'),
            'icon': 'terms_closed',
        },
    }
    term_id = terms.simplify_terms_of_use(terms_of_use)
    return term_to_image_mapping.get(term_id, None)


def get_terms_of_use_url(terms_of_use):
    terms_of_use_url = url_for('/terms-of-use')
    pagemark = mapping_terms_of_use_to_pagemark.get(terms_of_use)
    if pagemark:
        terms_of_use_url += pagemark
    return terms_of_use_url


def get_dataset_terms_of_use(pkg):
    rights = logic.get_action('ogdch_dataset_terms_of_use')({}, {'id': pkg})
    return rights['dataset_rights']


def get_dataset_by_identifier(identifier):
    try:
        return logic.get_action('ogdch_dataset_by_identifier')(
            {'for_view': True},
            {'identifier': identifier}
        )
    except logic.NotFound:
        return None


def get_readable_file_size(num, suffix='B'):
    if not num:
        return False
    try:
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            num = float(num)
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Y', suffix)
    except ValueError:
        return False


def get_piwik_config():
    return {
        'url': tk.config.get('piwik.url', False),
        'site_id': tk.config.get('piwik.site_id', False),
        'custom_dimension_action_organization_id': tk.config.get('piwik.custom_dimension_action_organization_id', False),  # noqa
        'custom_dimension_action_dataset_id': tk.config.get('piwik.custom_dimension_action_dataset_id', False),  # noqa
        'custom_dimension_action_format_id': tk.config.get('piwik.custom_dimension_action_format_id', False)  # noqa
    }


def ogdch_localised_number(number):
    # use swissgerman formatting rules when current language is german
    if i18n.get_lang() == 'de':
        return numbers.format_number(number, locale='de_CH')
    else:
        return localised_number(number)


def ogdch_render_tree():
    '''Returns HTML for a hierarchy of all publishers'''
    top_nodes = ogdch_group_tree()
    return _render_tree(top_nodes)


def _render_tree(top_nodes):
    '''Renders a tree of nodes. 10x faster than Jinja/organization_tree.html
    Note: avoids the slow url_for routine.
    '''
    html = '<ul id="organizations-list">'
    for node in top_nodes:
        html += _render_tree_node(node)
    return html + '</ul>'


def _render_tree_node(node):
    html = '<div class="organization-row">'
    html += '<a href="/%s/organization/%s">%s</a>' % (i18n.get_lang(), node['name'], node['title'])  # noqa
    html += '</div>'
    if node['children']:
        html += '<ul>'
        for child in node['children']:
            html += _render_tree_node(child)
        html += '</ul>'
    html = '<li id="node_%s" class="organization">%s</li>' % (node['name'], html)  # noqa
    return html


def ogdch_group_tree(type_='organization'):
    organizations = tk.get_action('group_tree')(
        {},
        {'type': type_, 'all_fields': True}
    )
    organizations = get_sorted_orgs_by_translated_title(organizations)
    return organizations


def get_sorted_orgs_by_translated_title(organizations):
    for organization in organizations:
        organization['title'] = loc.get_localized_value_from_json(organization['title'], i18n.get_lang())  # noqa
        if organization['children']:
            organization['children'] = get_sorted_orgs_by_translated_title(organization['children'])  # noqa

    organizations.sort(key=lambda org: strip_accents(org['title'].lower()), reverse=False)  # noqa
    return organizations


# this function strips characters with accents, cedilla and umlauts to their
# single character-representation to make the resulting words sortable
# See: http://stackoverflow.com/a/518232
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')  # noqa


def get_showcases_for_dataset(id):
    '''
    Return a list of showcases a dataset is associated with
    '''
    context = {'model': model, 'session': model.Session,
               'user': tk.c.user or tk.c.author, 'for_view': True,
               'auth_user_obj': tk.c.userobj}
    data_dict = {'package_id': id}

    try:
        return tk.get_action('ckanext_package_showcase_list')(
            context, data_dict)
    except logic.NotFound:
        return None


def get_localized_newsletter_url():
    current_language = lang()
    newsletter_url = {
       'en': None,
       'de': 'https://www.bfs.admin.ch/bfs/de/home/dienstleistungen/ogd/newsmail.html',  # noqa
       'fr': 'https://www.bfs.admin.ch/bfs/fr/home/services/ogd/newsmail.html',
       'it': 'https://www.bfs.admin.ch/bfs/it/home/servizi/ogd/newsmail.html',
    }
    return newsletter_url[current_language]
