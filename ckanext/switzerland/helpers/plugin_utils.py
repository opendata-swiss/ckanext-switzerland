import yaml
import os
import json
import re
import urlparse
from ckan import logic
import ckan.plugins.toolkit as toolkit
from ckan.lib.munge import munge_title_to_name
import ckanext.switzerland.helpers.frontend as sh
import ckanext.switzerland.helpers.localize as localize

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


class FormatMappingNotLoadedError(Exception):
    pass


def ogdch_get_format_mapping():
    """gets the format mapping from  a file for ogdch controller plugins"""
    try:
        mapping_path = os.path.join(__location__, 'mapping.yaml')
        with open(mapping_path, 'r') as format_mapping_file:
            format_mapping = yaml.safe_load(format_mapping_file)
    except (IOError, yaml.YAMLError) as exception:
        raise FormatMappingNotLoadedError(
            'Loading Format-Mapping from Path: (%s) '
            'failed with Exception: (%s)'
            % (mapping_path, exception)
        )
    else:
        return format_mapping


def _prepare_package_json(pkg_dict, format_mapping, ignore_fields):
    # parse all json strings in dict
    pkg_dict = _package_parse_json_strings(pkg_dict)

    # map ckan fields
    pkg_dict = _package_map_ckan_default_fields(pkg_dict)

    # prepare format of resources
    pkg_dict = _prepare_resources_format(
        pkg_dict=pkg_dict, format_mapping=format_mapping)

    try:
        # Do not change the resulting dict for API requests
        path = toolkit.request.path
        if any([
            path.startswith('/api'),
            path.endswith('.xml'),
            path.endswith('.rdf'),
            path.endswith('.n3'),
            path.endswith('.ttl'),
            path.endswith('.jsonld'),

        ]):
            return pkg_dict
    except TypeError:
        # we get here if there is no request (i.e. on the command line)
        return pkg_dict

    # replace langauge dicts with requested language strings
    desired_lang_code = _get_request_language()
    pkg_dict = _package_reduce_to_requested_language(
        pkg_dict, desired_lang_code,
        ignore_fields=ignore_fields
    )

    return pkg_dict


def _get_request_language():
    try:
        return toolkit.request.environ['CKAN_LANG']
    except TypeError:
        return toolkit.config.get('ckan.locale_default', 'en')


def _package_parse_json_strings(pkg_dict):
    # try to parse all values as JSON
    for key, value in pkg_dict.iteritems():
        pkg_dict[key] = sh.parse_json(value)

    # groups
    if 'groups' in pkg_dict and pkg_dict['groups'] is not None:
        for group in pkg_dict['groups']:
            """
            TODO: somehow the title is messed up here,
            but the display_name is okay
            """
            group['title'] = group['display_name']
            for field in group:
                group[field] = sh.parse_json(group[field])

    # organization
    if 'organization' in pkg_dict and pkg_dict['organization'] is not None:
        for field in pkg_dict['organization']:
            pkg_dict['organization'][field] = sh.parse_json(
                pkg_dict['organization'][field]
            )

    return pkg_dict


def _package_map_ckan_default_fields(pkg_dict):  # noqa
    pkg_dict['display_name'] = pkg_dict['title']

    if pkg_dict.get('maintainer') is None:
        try:
            pkg_dict['maintainer'] = pkg_dict['contact_points'][0]['name']  # noqa
        except (KeyError, IndexError):
            pass

    if pkg_dict.get('maintainer_email') is None:
        try:
            pkg_dict['maintainer_email'] = pkg_dict['contact_points'][0]['email']  # noqa
        except (KeyError, IndexError):
            pass

    if pkg_dict.get('author') is None:
        try:
            pkg_dict['author'] = pkg_dict['publishers'][0]['label']  # noqa
        except (KeyError, IndexError):
            pass

    if pkg_dict.get('resources') is not None:
        for resource in pkg_dict['resources']:
            resource['name'] = resource['title']

    return pkg_dict


def _prepare_resources_format(pkg_dict, format_mapping):
    if pkg_dict.get('resources') is not None:
        for resource in pkg_dict['resources']:
            resource = _prepare_resource_format(
                resource=resource,
                format_mapping=format_mapping)

            # if format could not be mapped and media_type exists use this value  # noqa
            if (not resource.get('format') and resource.get('media_type')):
                resource['format'] = resource['media_type'].split('/')[-1]

    return pkg_dict


# Generates format of resource and saves it in format field
def _prepare_resource_format(resource, format_mapping):
    resource_format = ''

    # get format from media_type field if available
    if not resource_format and resource.get('media_type'):  # noqa
        resource_format = resource['media_type'].split('/')[-1].lower()

    # get format from format field if available (lol)
    if not resource_format and resource.get('format'):
        resource_format = resource['format'].split('/')[-1].lower()

    # check if 'media_type' or 'format' can be mapped
    has_format = (sh.map_to_valid_format(
        resource_format,
        format_mapping
    ) is not None)

    # if the fields can't be mapped,
    # try to parse the download_url as a last resort
    if not has_format and resource.get('download_url'):
        path = urlparse.urlparse(resource['download_url']).path
        ext = os.path.splitext(path)[1]
        if ext:
            resource_format = ext.replace('.', '').lower()

    mapped_format = sh.map_to_valid_format(
        resource_format,
        format_mapping
    )
    if mapped_format:
        # if format could be successfully mapped write it to format field
        resource['format'] = mapped_format
    elif not resource.get('download_url'):
        resource['format'] = 'SERVICE'
    else:
        # else return empty string (this will be indexed as N/A)
        resource['format'] = ''

    return resource


def _package_reduce_to_requested_language(pkg_dict, desired_lang_code, ignore_fields):  # noqa
    # pkg fields
    for key, value in pkg_dict.iteritems():
        if key not in ignore_fields:
            pkg_dict[key] = _extract_lang_value(
                value,
                desired_lang_code
            )

    # groups
    pkg_dict = _reduce_group_language(pkg_dict, desired_lang_code)

    # organization
    pkg_dict = _reduce_org_language(pkg_dict, desired_lang_code)

    # resources
    pkg_dict = _reduce_res_language(pkg_dict, desired_lang_code)

    return pkg_dict


def _reduce_group_language(pkg_dict, desired_lang_code):
    if 'groups' in pkg_dict and pkg_dict['groups'] is not None:
        try:
            for element in pkg_dict['groups']:
                for field in element:
                    element[field] = _extract_lang_value(
                        element[field],
                        desired_lang_code
                    )
        except TypeError:
            pass

    return pkg_dict


def _reduce_org_language(pkg_dict, desired_lang_code):
    if 'organization' in pkg_dict and pkg_dict['organization'] is not None:
        try:
            for field in pkg_dict['organization']:
                pkg_dict['organization'][field] = _extract_lang_value(
                    pkg_dict['organization'][field],
                    desired_lang_code
                )
        except TypeError:
            pass
    return pkg_dict


def _reduce_res_language(pkg_dict, desired_lang_code):
    if 'resources' in pkg_dict and pkg_dict['resources'] is not None:
        try:
            for element in pkg_dict['resources']:
                for field in element:
                    element[field] = _extract_lang_value(
                        element[field],
                        desired_lang_code
                    )
        except TypeError:
            pass
    return pkg_dict


def _extract_lang_value(value, lang_code):
    new_value = sh.parse_json(value)

    if isinstance(new_value, dict):
        return sh.get_localized_value(
            new_value,
            lang_code,
            default_value=''
        )
    return value


def _prepare_suggest_context(search_data, pkg_dict):
    def clean_suggestion(term):
        return term.replace('-', '')

    search_data['suggest_groups'] = [clean_suggestion(t['name']) for t in pkg_dict['groups']]  # noqa
    search_data['suggest_organization'] = clean_suggestion(pkg_dict['organization']['name'])  # noqa

    search_data['suggest_tags'] = []
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_de', [])])  # noqa
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_fr', [])])  # noqa
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_it', [])])  # noqa
    search_data['suggest_tags'].extend([clean_suggestion(t) for t in search_data.get('keywords_en', [])])  # noqa

    search_data['suggest_res_rights'] = [clean_suggestion(t) for t in search_data['res_rights']]  # noqa
    search_data['suggest_res_format'] = [clean_suggestion(t) for t in search_data['res_format']]  # noqa

    return search_data


def _prepare_formats_for_index(resources, format_mapping):
    """generates a set with formats of all resources"""
    formats = set()
    for r in resources:
        resource = _prepare_resource_format(
            resource=r,
            format_mapping=format_mapping
        )
        if resource['format']:
            formats.add(resource['format'])
        else:
            formats.add('N/A')

    return list(formats)


def _is_dataset_package_type(pkg_dict):
    """determines whether a packages is a dataset"""
    try:
        return (pkg_dict['type'] == 'dataset')
    except KeyError:
        return False


def ogdch_prepare_search_data_for_index(search_data, format_mapping):
    """prepares the data for indexing"""
    if not _is_dataset_package_type(search_data):
        return search_data

    extract_title = LangToString('title')
    validated_dict = json.loads(search_data['validated_data_dict'])

    search_data['res_name'] = [extract_title(r) for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_en'] = [sh.get_localized_value(r['title'], 'en') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_de'] = [sh.get_localized_value(r['title'], 'de') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_fr'] = [sh.get_localized_value(r['title'], 'fr') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_it'] = [sh.get_localized_value(r['title'], 'it') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_en'] = [sh.get_localized_value(r['description'], 'en') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_de'] = [sh.get_localized_value(r['description'], 'de') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_fr'] = [sh.get_localized_value(r['description'], 'fr') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_it'] = [sh.get_localized_value(r['description'], 'it') for r in validated_dict[u'resources']]  # noqa
    search_data['groups_en'] = [sh.get_localized_value(g['display_name'], 'en') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_de'] = [sh.get_localized_value(g['display_name'], 'de') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_fr'] = [sh.get_localized_value(g['display_name'], 'fr') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_it'] = [sh.get_localized_value(g['display_name'], 'it') for g in validated_dict[u'groups']]  # noqa
    search_data['res_description'] = [LangToString('description')(r) for r in validated_dict[u'resources']]  # noqa
    search_data['res_format'] = _prepare_formats_for_index(
        resources=validated_dict[u'resources'],
        format_mapping=format_mapping
    )  # noqa
    search_data['res_rights'] = [sh.simplify_terms_of_use(r['rights']) for r in validated_dict[u'resources'] if 'rights' in r.keys()]  # noqa
    search_data['title_string'] = extract_title(validated_dict)
    search_data['description'] = LangToString('description')(validated_dict)  # noqa
    if 'political_level' in validated_dict[u'organization']:
        search_data['political_level'] = validated_dict[u'organization'][u'political_level']  # noqa

    search_data['identifier'] = validated_dict.get('identifier')
    search_data['contact_points'] = [c['name'] for c in validated_dict.get('contact_points', [])]  # noqa
    search_data['publishers'] = [p['label'] for p in validated_dict.get('publishers', [])]  # noqa

    # TODO: Remove the try-except-block.
    # This fixes the index while we have 'wrong' relations on
    # datasets harvested with an old version of ckanext-geocat
    try:
        search_data['see_alsos'] = [d['dataset_identifier'] for d in validated_dict.get('see_alsos', [])]  # noqa
    except TypeError:
        search_data['see_alsos'] = [d for d in
                                    validated_dict.get('see_alsos',
                                                       [])]  # noqa

    # make sure we're not dealing with NoneType
    if search_data['metadata_created'] is None:
        search_data['metadata_created'] = ''

    if search_data['metadata_modified'] is None:
        search_data['metadata_modified'] = ''

    try:
        # index language-specific values (or it's fallback)
        for lang_code in sh.get_langs():
            search_data['title_' + lang_code] = sh.get_localized_value(
                validated_dict['title'],
                lang_code
            )
            search_data['title_string_' + lang_code] = munge_title_to_name(
                sh.get_localized_value(validated_dict['title'], lang_code)
            )
            search_data['description_' + lang_code] = sh.get_localized_value(  # noqa
                validated_dict['description'],
                lang_code
            )
            search_data['keywords_' + lang_code] = sh.get_localized_value(
                validated_dict['keywords'],
                lang_code
            )
            search_data['organization_' + lang_code] = sh.get_localized_value(  # noqa
                validated_dict['organization']['title'],
                lang_code
            )

    except KeyError:
        pass

    # clean terms for suggest context
    search_data = _prepare_suggest_context(
        search_data,
        validated_dict
    )

    return search_data


class LangToString(object):
    """language to string"""
    def __init__(self, attribute):
        self.attribute = attribute

    def __call__(self, data_dict):
        try:
            lang = data_dict[self.attribute]
            return (
                '%s - %s - %s - %s' % (
                    lang.get('de', ''),
                    lang.get('fr', ''),
                    lang.get('it', ''),
                    lang.get('en', '')
                )
            )
        except KeyError:
            return ''


def ogdch_prepare_res_dict_before_show(
        res_dict, format_mapping, ignore_fields):
    """prepares a resource dict for the template"""
    res_dict = _prepare_package_json(
            pkg_dict=res_dict,
            format_mapping=format_mapping,
            ignore_fields=ignore_fields
        )
    res_dict = _prepare_resource_format(
        resource=res_dict, format_mapping=format_mapping)

    # if format could not be mapped and media_type exists use this value
    if not res_dict.get('format') and res_dict.get('media_type'):
        res_dict['format'] = res_dict['media_type'].split('/')[-1]

    return res_dict


def ogdch_prepare_pkg_dict_for_api(pkg_dict):
    if not _is_dataset_package_type(pkg_dict):
        return pkg_dict

    pkg_dict = _package_map_ckan_default_fields(pkg_dict)

    # groups
    if pkg_dict['groups'] is not None:
        for group in pkg_dict['groups']:
            """
            TODO: somehow the title is messed up here,
            but the display_name is okay
            """
            group['title'] = group['display_name']
            for field in group:
                group[field] = sh.parse_json(group[field])

    # load organization from API to get all fields defined in schema
    # by default, CKAN loads organizations only from the database
    if pkg_dict['owner_org'] is not None:
        pkg_dict['organization'] = logic.get_action('organization_show')(
            {},
            {
                'id': pkg_dict['owner_org'],
                'include_users': False,
                'include_followers': False,
            }
        )

    return pkg_dict


def ogdch_adjust_search_params(search_params):
    """search in correct language-specific field and boost
    results in current language
    borrowed from ckanext-multilingual (core extension)"""
    lang_set = sh.get_langs()
    try:
        current_lang = toolkit.request.environ['CKAN_LANG']
    except TypeError as err:
        if err.message == ('No object (name: request) has been registered '
                           'for this thread'):
            # This happens when this code gets called as part of a paster
            # command rather then as part of an HTTP request.
            current_lang = toolkit.config.get('ckan.locale_default')
        else:
            raise

    # fallback to default locale if locale not in suported langs
    if current_lang not in lang_set:
        current_lang = toolkit.config.get('ckan.locale_default', 'en')
    # treat current lang differenly so remove from set
    lang_set.remove(current_lang)

    # add default query field(s)
    query_fields = 'text'

    # weight current lang more highly
    query_fields += ' title_%s^8 text_%s^4' % (current_lang, current_lang)

    for lang in lang_set:
        query_fields += ' title_%s^2 text_%s' % (lang, lang)

    search_params['qf'] = query_fields

    '''
    Unless the query is already being filtered by any type
    (either positively, or negatively), reduce to only display
    'dataset' type
    This is done because by standard all types are displayed, this
    leads to strange situations where e.g. harvest sources are shown
    on organization pages.
    TODO: fix issue https://github.com/ckan/ckan/issues/2803 in CKAN core
    '''
    fq = search_params.get('fq', '')
    if 'dataset_type:' not in fq:
        search_params.update({'fq': "%s +dataset_type:dataset" % fq})

    # remove colon followed by a space from q to avoid false negatives
    q = search_params.get('q', '')
    search_params['q'] = re.sub(":\s", " ", q)

    return search_params
