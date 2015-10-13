from collections import OrderedDict
from ckan.plugins.toolkit import get_or_bust, side_effect_free, ObjectNotFound
from ckan.logic import NotFound
import ckan.plugins.toolkit as tk


@side_effect_free
def ogdch_dataset_count(context, data_dict):
    '''
    Return the total number of datasets and the number of dataset per group.
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True},{})
    req_context = {'user': user['name']}

    # group_list contains the number of datasets in the 'packages' field
    groups = tk.get_action('group_list')(req_context, {'all_fields': True})
    groups = sorted(groups, key=lambda group: group['packages'])[::-1]
    group_count = OrderedDict()
    for group in groups:
        group_count[group['name']] = group['packages']


    # get the total number of dataset from package_search
    search_result = tk.get_action('package_search')(req_context, {'rows': 0})

    return {
        'total_count': search_result['count'],
        'groups': group_count,
    }

@side_effect_free
def ogdch_dataset_terms_of_use(context, data_dict):
    '''
    Returns the terms of use for the requested dataset.

    By definition the terms of use of a dataset corresponds 
    to the least open rights statement of all distributions of
    the dataset
    '''
    terms = [
      'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
      'NonCommercialAllowed-CommercialAllowed-ReferenceRequired',
      'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired',
      'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired',
      'ClosedData',
    ]
    user = tk.get_action('get_site_user')({'ignore_auth': True},{})
    req_context = {'user': user['name']}
    pkg_id = get_or_bust(data_dict, 'id')
    pkg = tk.get_action('package_show')(req_context, {'id': pkg_id})

    least_open = None
    for res in pkg['resources']:
        if res['rights'] not in terms:
            least_open = 'ClosedData'
            continue
        if least_open is None:
            least_open = res['rights']
            continue
        if terms.index(res['rights']) > terms.index(least_open):
            least_open = res['rights']

    if least_open is None:
        least_open = 'ClosedData'

    return {
        'dataset_rights': least_open
    }

@side_effect_free
def ogdch_dataset_by_identifier(context, data_dict):
    user = tk.get_action('get_site_user')({'ignore_auth': True},{})
    req_context = {'user': user['name']}
    identifier = get_or_bust(data_dict, 'identifier')

    param = 'identifier:%s' % identifier
    result = tk.get_action('package_search')(req_context, {'fq': param })
    try:
        return result['results'][0]
    except (KeyError, IndexError, TypeError):
        raise NotFound
