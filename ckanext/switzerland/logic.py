from collections import OrderedDict
from ckan.plugins.toolkit import get_or_bust, side_effect_free, ObjectNotFound
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
