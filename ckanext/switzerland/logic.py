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
    mapping = {'packages': 'count', 'name': 'name'}
    groups = [dict((new_key, group[old_key]) for old_key, new_key in mapping.iteritems()) for group in groups]

    # get the total number of dataset from package_search
    search_result = tk.get_action('package_search')(req_context, {'rows': 0})

    return {
        'total_count': search_result['count'],
        'groups': groups,
    }
