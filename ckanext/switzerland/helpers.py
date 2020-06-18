# coding=UTF-8

import os
import ckan.plugins.toolkit as tk
import ckan.logic as logic
from ckan import model as model
from ckan.exceptions import CkanConfigurationException
import requests
import json
from ckan.common import _
from babel import numbers
import iribaker
from urlparse import urlparse

from ckan.lib.helpers import lang, url_for, localised_number
import ckan.lib.i18n as i18n
import unicodedata

import logging
log = logging.getLogger(__name__)

TERMS_OF_USE_OPEN = 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired' # noqa
TERMS_OF_USE_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired' # noqa
TERMS_OF_USE_CLOSED = 'ClosedData'

# these bookmarks can be used in the wordpress page
# for the terms of use
mapping_terms_of_use_to_pagemark = {
    TERMS_OF_USE_OPEN: '#terms_open',
    TERMS_OF_USE_BY: '#terms_by',
    TERMS_OF_USE_ASK: '#terms_ask',
    TERMS_OF_USE_BY_ASK: '#terms_by_ask',
}

showcase_types_mapping = {
    "application": u'{"fr": "Application", "de": "Applikation", "en": "Application", "it": "Applicazione"}', # noqa
    "data_visualization": u'{"fr": "Visualisation de donées", "de": "Daten-Visualisierung", "en": "Data visualization", "it": "Visualizzazione di dati"}', # noqa
    "event": u'{"fr": "Evènement", "de": "Veranstaltung", "en": "Event", "it": "Manifestazione"}', # noqa
    "blog_and_media_articles": u'{"fr": "Article blogs et médias", "de": "Blog und Medienartikel", "en": "Blog and media article", "it": "Blog/articolo"}', # noqa
    "paper": u'{"fr": "Article scientifique", "de": "Wissenschaftliche Arbeit", "en": "Paper", "it": "Articolo scientifico"}', # noqa
    "best_practice": u'{"fr": "Best practice", "de": "Best practice", "en": "Best practice", "it": "Best practice"}', # noqa
}


def get_dataset_count(dataset_type='dataset'):
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    fq = ''.join(['+dataset_type:', dataset_type])
    packages = tk.get_action('package_search')(
        req_context,
        {'fq': fq}
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
        return get_localized_value(
            lang_dict,
            default_value=facet_item['display_name']
        )
    except:
        return facet_item['display_name']


def get_langs():
    language_priorities = ['en', 'de', 'fr', 'it']
    return language_priorities


def get_localized_value(lang_dict, desired_lang_code=None, default_value=''):
    # return original value if it's not a dict
    if not isinstance(lang_dict, dict):
        return lang_dict

    """
    if this is not a proper lang_dict ('de', 'fr', etc. keys),
    return original value
    """
    if not all(k in lang_dict for k in get_langs()):
        return lang_dict

    # if no specific lang is requested, read from environment
    if desired_lang_code is None:
        desired_lang_code = tk.request.environ['CKAN_LANG']

    try:
        # return desired lang if available
        if lang_dict[desired_lang_code]:
            return lang_dict[desired_lang_code]
    except KeyError:
        pass

    return _lang_fallback(lang_dict, default_value)


def _lang_fallback(lang_dict, default_value):
    # loop over languages in order of their priority for fallback
    for lang_code in get_langs():
        try:
            if (isinstance(lang_dict[lang_code], basestring) and
                    lang_dict[lang_code]):
                return lang_dict[lang_code]
        except (KeyError, IndexError, ValueError):
            continue
    return default_value


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
        TERMS_OF_USE_OPEN: {  # noqa
            'title': _('Open use'),
            'icon': 'terms_open',
        },
        TERMS_OF_USE_BY: {  # noqa
            'title': _('Open use. Must provide the source.'),
            'icon': 'terms_by',
        },
        TERMS_OF_USE_ASK: {  # noqa
            'title': _('Open use. Use for commercial purposes requires permission of the data owner.'),  # noqa
            'icon': 'terms_ask',
        },
        TERMS_OF_USE_BY_ASK: {  # noqa
            'title': _('Open use. Must provide the source. Use for commercial purposes requires permission of the data owner.'),  # noqa
            'icon': 'terms_by-ask',
        },
        TERMS_OF_USE_CLOSED: {
            'title': _('Closed data'),
            'icon': 'terms_closed',
        },
    }
    term_id = simplify_terms_of_use(terms_of_use)
    return term_to_image_mapping.get(term_id, None)


def get_terms_of_use_url(terms_of_use):
    terms_of_use_url = url_for('/terms-of-use')
    pagemark = mapping_terms_of_use_to_pagemark.get(terms_of_use)
    if pagemark:
        terms_of_use_url += pagemark
    return terms_of_use_url


def simplify_terms_of_use(term_id):
    terms = [
        TERMS_OF_USE_OPEN,
        TERMS_OF_USE_BY,
        TERMS_OF_USE_ASK,
        TERMS_OF_USE_BY_ASK,
    ]

    if term_id in terms:
        return term_id
    return 'ClosedData'


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


def parse_json(value, default_value=None):
    try:
        return json.loads(value)
    except (ValueError, TypeError, AttributeError):
        if default_value is not None:
            return default_value
        return value


def get_content_headers(url):
    response = requests.head(url)
    return response


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
        organization['title'] = get_translated_group_title(organization['title'])  # noqa
        if organization['children']:
            organization['children'] = get_sorted_orgs_by_translated_title(organization['children'])  # noqa

    organizations.sort(key=lambda org: strip_accents(org['title'].lower()), reverse=False)  # noqa
    return organizations


def get_translated_group_title(titles_string):
    group_titles_dict = parse_json(titles_string)
    return get_localized_value(
        group_titles_dict,
        i18n.get_lang(),
        titles_string
    )


# this function strips characters with accents, cedilla and umlauts to their
# single character-representation to make the resulting words sortable
# See: http://stackoverflow.com/a/518232
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')  # noqa


# all formats that need to be mapped have to be entered in the mapping.yaml
def map_to_valid_format(resource_format, format_mapping):
    resource_format_lower = resource_format.lower()
    for key, values in format_mapping.iteritems():
        if resource_format_lower in values:
            return key
    else:
        return None


# convert URI to IRI (used for RDF)
# this function also validates the URI and throws a ValueError if the
# provided URI is invalid
def uri_to_iri(uri):
    result = urlparse(uri)
    if not result.scheme or not result.netloc or result.netloc == '-':
        raise ValueError("Provided URI does not have a valid schema or netloc")

    try:
        iri = iribaker.to_iri(uri)
        return iri
    except:
        raise ValueError("Provided URI can't be converted to IRI")


def get_shacl_command_from_config():
    shacl_command = tk.config.get('ckanext.switzerland.shacl_command_path')
    if not shacl_command:
        raise CkanConfigurationException(
            """'ckanext.switzerland.shacl_command_path'
            setting is missing in config file""")
    return shacl_command


def get_shacl_resultsdir_from_config():
    shacl_results_dir = tk.config.get('ckanext.switzerland.shacl_results_dir')
    if not shacl_results_dir:
        raise CkanConfigurationException(
            """'ckanext.switzerland.shacl_results_dir'
            setting is missing in config file""")
    return shacl_results_dir


def get_shacl_shapesdir_from_config():
    shacl_shapesdir = tk.config.get('ckanext.switzerland.shacl_shapes_dir')
    if not shacl_shapesdir:
        raise CkanConfigurationException(
            """'ckanext.switzerland.shacl_shapes_dir'
            setting is missing in config file""")
    return shacl_shapesdir


def get_shacl_shape_file_path(filename):
    shapesdir = get_shacl_shapesdir_from_config()
    return os.path.join(shapesdir, filename)


def make_shacl_results_dir(harvest_source_id):
    resultdir = os.path.join(
        get_shacl_resultsdir_from_config(),
        harvest_source_id)
    try:
        os.makedirs(resultdir)
    except OSError:
        pass
    return resultdir


def get_shacl_file_path(resultdir, identifier, format):
    filename = '.'.join([identifier, format])
    filepath = os.path.join(resultdir, filename)
    return filepath


def get_shacl_result_file_path(resultdir, shapefile, format):
    identifier = shapefile.split('.')[0]
    filename = '.'.join(['result', identifier, format])
    filepath = os.path.join(resultdir, filename)
    return filepath


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


def create_showcase_types():
    """
    Create tags and vocabulary for showcase types, if they don't exist already.
    """
    user = tk.get_action("get_site_user")({"ignore_auth": True}, ())
    context = {"user": user["name"]}
    try:
        # TODO: this is a workaround copied from
        # https://github.com/ckan/ckanext-dcat/commit/bd490115da8087a14b9a2ef603328e69535144bb
        # It is necessary "until the core translation function defaults to the
        # Flask one." When we upgrade CKAN to v2.9, we should try removing it.
        from paste.registry import Registry
        from ckan.lib.cli import MockTranslator
        registry = Registry()
        registry.prepare()
        from pylons import translator
        registry.register(translator, MockTranslator())
        # End of workaround

        data = {"id": "showcase_types"}
        tk.get_action("vocabulary_show")(context, data)
        log.info("'showcase_types' vocabulary already exists, skipping")
    except tk.ObjectNotFound:
        log.info("Creating vocab 'showcase_types'")
        data = {"name": "showcase_types"}
        vocab = tk.get_action("vocabulary_create")(context, data)
        for tag in showcase_types_mapping.keys():
            log.info("Adding tag {0} to vocab 'showcase_types'".format(tag))
            data = {"name": tag, "vocabulary_id": vocab["id"]}
            tk.get_action("tag_create")(context, data)


def showcase_types():
    """
    Return the list of showcase types from the showcase_types vocabulary.
    """
    create_showcase_types()
    try:
        showcase_types = tk.get_action("tag_list")(
            data_dict={"vocabulary_id": "showcase_types"}
        )
        return showcase_types
    except tk.ObjectNotFound:
        return None


def get_showcase_type_name(showcase_type):
    type_string = showcase_types_mapping.get(showcase_type, showcase_type)
    return get_localized_value(parse_json(type_string))


def group_name_in_groups(group_name, groups):
    for group in groups:
        if group_name == group['name']:
            return True
    return False


def get_localized_group_list():
    """
    Returns a list of dicts containing the id, name and localized title
    for each group.
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    groups = tk.get_action('group_list')(req_context, {'all_fields': True})
    group_list = []
    for group in groups:
        group_list.append({
            'id': group['id'],
            'name': group['name'],
            'title': get_localized_value(group['title'], i18n.get_lang()),
        })

    group_list.sort(key=lambda group: strip_accents(group['title'].lower()), reverse=False)  # noqa
    return group_list
