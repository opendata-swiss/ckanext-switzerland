import ckan.plugins.toolkit as tk
import requests
from pylons import config

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
    api_url = config.get('ckanext.switzerland.wp_ajax_url', None)
    try:
        r = requests.post(api_url, data={'action': action})
        return r.json()
    except:
        return None
