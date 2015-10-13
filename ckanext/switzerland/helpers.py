import ckan.plugins.toolkit as tk
import ckan.logic as logic
import requests
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

def get_localized_org(org=None, include_datasets=False):
    if org is None:
        return {}
    try:
        lang_code = pylons.request.environ['CKAN_LANG']
        org = logic.get_action('organization_show')(
            {}, {'id': org, 'include_datasets': include_datasets})
        for key, value in org.iteritems():
            org[key] = _get_language_value(value, lang_code, default_value=value)
        return org

    except (logic.NotFound, logic.ValidationError, logic.NotAuthorized, AttributeError):
        return {}

LANGUAGE_PRIORITIES = ['de', 'en', 'fr', 'it'] 
def _get_language_value(lang_dict, desired_lang_code, default_value=''):
    if not isinstance(lang_dict, dict):
        return default_value

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
      'http://purl.org/cld/freq/weekly': _('Weekly'),
      'http://purl.org/cld/freq/monthly': _('Monthly'),
      'http://purl.org/cld/freq/semiannual': _('Semi Annual'),
      'http://purl.org/cld/freq/annual': _('Annual'),
    }
    try:
        return frequencies[identifier]
    except KeyError:
        return identifier

def get_terms_of_use_icon(terms_of_use):
    term_to_image_mapping = {
      'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired': 'terms_open.svg',
      'NonCommercialAllowed-CommercialAllowed-ReferenceRequired': 'terms_ref.svg',
      'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired': 'terms_ask.svg',
      'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired': 'terms_ref-ask.svg',
    }
    try:
        return term_to_image_mapping[terms_of_use]
    except KeyError:
        return False
