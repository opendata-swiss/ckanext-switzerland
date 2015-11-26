import ckan.plugins.toolkit as tk
import ckan.logic as logic
import requests
import json
import pylons
from ckan.common import _

import logging
log = logging.getLogger(__name__)

def get_dataset_count():
    user = tk.get_action('get_site_user')({'ignore_auth': True},{})
    req_context = {'user': user['name']}

    packages = tk.get_action('package_search')(req_context, {'fq': '+dataset_type:dataset'})
    return packages['count']

def get_group_count():
    '''
    Return the number of groups
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True},{})
    req_context = {'user': user['name']}
    groups = tk.get_action('group_list')(req_context, {})
    return len(groups)

def get_org_count():
    user = tk.get_action('get_site_user')({'ignore_auth': True},{})
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
        r = requests.post(api_url, data={'action': action})
        return r.json()
    except:
        return None

def get_localized_org(org_id=None, include_datasets=False):
    if not org_id or org_id is None:
        return {}
    try:
        return logic.get_action('organization_show')(
               {'for_view': True}, {'id': org_id, 'include_datasets': include_datasets})
    except (logic.NotFound, logic.ValidationError, logic.NotAuthorized, AttributeError):
        return {}

def localize_json_title(facet_item):
    try:
        lang_dict = json.loads(facet_item['display_name'])
        return get_localized_value(lang_dict, default_value=facet_item['display_name'])
    except:
        return facet_item['display_name']

LANGUAGE_PRIORITIES = ['en', 'de', 'fr', 'it'] 
def get_localized_value(lang_dict, desired_lang_code=None, default_value=''):
    # return original value if it's not a dict
    if not isinstance(lang_dict, dict):
        return lang_dict

    # if this is not a proper lang_dict ('de', 'fr', etc. keys), return original value
    if not all(k in lang_dict for k in LANGUAGE_PRIORITIES):
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

    # loop over languages in order of their priority for fallback
    for lang_code in LANGUAGE_PRIORITIES:
        try:
            if isinstance(lang_dict[lang_code], basestring) and lang_dict[lang_code]:
                return lang_dict[lang_code]
        except (KeyError, IndexError, ValueError):
            continue
    return default_value

def get_frequency_name(identifier):
    frequencies = {
      'http://purl.org/cld/freq/completelyIrregular': _('Irregular'),
      'http://purl.org/cld/freq/continuous': _('Continuous'),
      'http://purl.org/cld/freq/daily': _('Daily'),
      'http://purl.org/cld/freq/threeTimesAWeek': _('Three times a week'),
      'http://purl.org/cld/freq/semiweekly': _('Semi weekly'),
      'http://purl.org/cld/freq/weekly': _('Weekly'),
      'http://purl.org/cld/freq/threeTimesAMonth': _('Three times a month'),
      'http://purl.org/cld/freq/biweekly': _('Biweekly'),
      'http://purl.org/cld/freq/semimonthly': _('Semimonthly'),
      'http://purl.org/cld/freq/monthly': _('Monthly'),
      'http://purl.org/cld/freq/bimonthly': _('Bimonthly'),
      'http://purl.org/cld/freq/quarterly': _('Quarterly'),
      'http://purl.org/cld/freq/threeTimesAYear': _('Three times a year'),
      'http://purl.org/cld/freq/semiannual': _('Semi Annual'),
      'http://purl.org/cld/freq/annual': _('Annual'),
      'http://purl.org/cld/freq/biennial': _('Biennial'),
      'http://purl.org/cld/freq/triennial': _('Triennial'),
    }
    try:
        return frequencies[identifier]
    except KeyError:
        return identifier

def get_terms_of_use_icon(terms_of_use):
    term_to_image_mapping = {
        'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired': {
            'title': _('Open data'),
            'icon': 'terms_open',
        },
        'NonCommercialAllowed-CommercialAllowed-ReferenceRequired': {
            'title': _('Reference required'),
            'icon': 'terms_by',
        },
        'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired': {
            'title': _('Commercial use with permission allowed'),
            'icon': 'terms_ask',
        },
        'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired': {
            'title': _('Reference required / Commercial use with permission allowed'),
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
        return logic.get_action('ogdch_dataset_by_identifier')({'for_view': True}, {'identifier': identifier})
    except logic.NotFound:
        return None

def get_readable_file_size(num, suffix='B'):
    try:
        for unit in ['','K','M','G','T','P','E','Z']:
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
    return { 'url': pylons.config.get('piwik.url', False), 'site_id': pylons.config.get('piwik.site_id', False)}
