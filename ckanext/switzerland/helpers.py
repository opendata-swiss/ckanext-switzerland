import ckan.plugins.toolkit as tk
import ckan.logic as logic
import requests
import json
import pylons
from ckan.common import _
from babel import numbers
from ckan.lib.helpers import localised_number
import ckan.lib.i18n as i18n

import unicodedata

import logging
log = logging.getLogger(__name__)


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
    return 'N/A'


def get_tweet_count():
    result = _call_wp_api('tweet_statistics')
    if result is not None:
        return result['data']['tweet_count']
    return 'N/A'


def _call_wp_api(action):
    api_url = pylons.config.get('ckanext.switzerland.wp_ajax_url', None)
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
        desired_lang_code = pylons.request.environ['CKAN_LANG']

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
        'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired': {  # noqa
            'title': _('Open data'),
            'icon': 'terms_open',
        },
        'NonCommercialAllowed-CommercialAllowed-ReferenceRequired': {  # noqa
            'title': _('Reference required'),
            'icon': 'terms_by',
        },
        'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired': {  # noqa
            'title': _('Commercial use with permission allowed'),
            'icon': 'terms_ask',
        },
        'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired': {  # noqa
            'title': _('Reference required / Commercial use with permission allowed'),  # noqa
            'icon': 'terms_by-ask',
        },
        'ClosedData': {
            'title': _('Closed data'),
            'icon': 'terms_closed',
        },
    }
    term_id = simplify_terms_of_use(terms_of_use)
    return term_to_image_mapping.get(term_id, None)


def simplify_terms_of_use(term_id):
    terms = [
        'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
        'NonCommercialAllowed-CommercialAllowed-ReferenceRequired',
        'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired',
        'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired',
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
        'url': pylons.config.get('piwik.url', False),
        'site_id': pylons.config.get('piwik.site_id', False)
    }


def ogdch_localised_number(number):
    # use swissgerman formatting rules when current language is german
    if i18n.get_lang() == 'de':
        return numbers.format_number(number, locale='de_CH')
    else:
        return localised_number(number)


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


# all formats that need to be mapped have to be entered lower-case
def map_to_valid_format(resource_format):
    format_mapping = {
        'CSV': ['csv', 'text (.csv)', 'comma ...'],
        'GeoJSON': ['geojson'],
        'GeoTIFF': ['geotiff'],
        'GPKG': ['gpkg'],
        'HTML': ['html'],
        'INTERLIS': ['interlis'],
        'JSON': ['json'],
        'KMZ': ['kmz'],
        'MULTIFORMAT': ['multiformat'],
        'ODS': ['ods', 'vnd.oas...', 'vnd.oasis.opendocument.spreadsheet'],
        'PC-AXIS': ['pc-axis file'],
        'PDF': ['pdf'],
        'PNG': ['png'],
        'RDF': ['sparql-...'],
        'SHAPEFILE': ['esri shapefile', 'esri geodatabase (....', 'esri file geodatabase', 'esri arcinfo ascii ...'], # noqa
        'TXT': ['text', 'txt', 'text (.txt)', 'plain'],
        'TIFF': ['tiff'],
        'WCS': ['wcs'],
        'WFS': ['wfs'],
        'WMS': ['wms'],
        'WMTS': ['wmts'],
        'XLS': ['xls', 'xlsx'],
        'XML': ['xml'],
        'ZIP': ['zip'],
    }
    resource_format_lower = resource_format.lower()
    for key, values in format_mapping.iteritems():
        if resource_format_lower in values:
            return key
    else:
        return None
