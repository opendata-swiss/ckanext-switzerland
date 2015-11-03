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

    packages = tk.get_action('package_search')(req_context, {})
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

def get_localized_pkg(pkg=None):
    if pkg is None:
        return {}
    try:
        pkg = logic.get_action('package_show')({}, {'id': pkg})
        for key, value in pkg.iteritems():
            pkg[key] = get_localized_value(value, default_value=value)
        return pkg
    except (logic.NotFound, logic.ValidationError, logic.NotAuthorized, AttributeError):
        return {}

def get_localized_org(org=None, include_datasets=False):
    if org is None:
        return {}
    try:
        org = logic.get_action('organization_show')(
            {}, {'id': org, 'include_datasets': include_datasets})
        for key, value in org.iteritems():
            org[key] = get_localized_value(value, default_value=value)
        return org
    except (logic.NotFound, logic.ValidationError, logic.NotAuthorized, AttributeError):
        return {}

def localize_json_title(facet_item):
    try:
        lang_dict = json.loads(facet_item['display_name'])
        return get_localized_value(lang_dict, default_value=facet_item['display_name'])
    except:
        return facet_item['display_name']

LANGUAGE_PRIORITIES = ['de', 'en', 'fr', 'it'] 
def get_localized_value(lang_dict, desired_lang_code=None, default_value=''):
    if not isinstance(lang_dict, dict):
        return default_value

    if desired_lang_code is None:
        desired_lang_code = pylons.request.environ['CKAN_LANG']

    try:
        if lang_dict[desired_lang_code]:
            return lang_dict[desired_lang_code]
    except KeyError:
        pass

    lang_idx = LANGUAGE_PRIORITIES.index(desired_lang_code)
    for i in range(0,len(LANGUAGE_PRIORITIES)):
        try:
            # choose next language according to priority
            lang_code = LANGUAGE_PRIORITIES[lang_idx-i]
            if str(lang_dict[lang_code]):
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
            'icon': 'terms_open.svg',
        },
        'NonCommercialAllowed-CommercialAllowed-ReferenceRequired': {
            'title': _('Reference required'),
            'icon': 'terms_by.svg',
        },
        'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired': {
            'title': _('Commercial use with permission allowed'),
            'icon': 'terms_ask.svg',
        },
        'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired': {
            'title': _('Reference required / Commercial use with permission allowed'),
            'icon': 'terms_by-ask.svg',
        },
        'ClosedData': {
            'title': _('Closed data'),
            'icon': 'terms_closed.svg',
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
        pkg = logic.get_action('ogdch_dataset_by_identifier')({}, {'identifier': identifier})
        return get_localized_pkg(pkg['id'])
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
