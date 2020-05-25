# coding=UTF-8

import os
import logging
import urlparse
import ckan.plugins.toolkit as toolkit
from ckan.lib.helpers import lang
import ckanext.switzerland.helpers as sh

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


class FormatMappingNotLoadedError(Exception):
    pass


def lang_to_string(data_dict, attribute):
    """make a long string with all 4 languages of an attribute"""
    value_dict = data_dict.get(attribute)
    value_string = ('%s - %s - %s - %s' % (
        value_dict.get('de', ''),
        value_dict.get('fr', ''),
        value_dict.get('it', ''),
        value_dict.get('en', '')
    ))
    return value_string


def prepare_suggest_context(search_data, pkg_dict):
    """prepares data for the suggest context"""
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


def get_request_language():
    try:
        return toolkit.request.environ['CKAN_LANG']
    except TypeError:
        return toolkit.config.get('ckan.locale_default', 'en')


def prepare_resource_format(resource, format_mapping):
    "prepares the format for a single resource"
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
        format_mapping,
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
        format_mapping,
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


def prepare_formats_for_index(resources, format_mapping):
    """generates a set with formats of all resources"""
    formats = set()
    for r in resources:
        resource = prepare_resource_format(
            resource=r, format_mapping=format_mapping)
        if resource['format']:
            formats.add(resource['format'])
        else:
            formats.add('N/A')
    return list(formats)


def prepare_resources_format(pkg_dict, format_mapping):
    if pkg_dict.get('resources') is not None:
        for resource in pkg_dict['resources']:
            resource = prepare_resource_format(
                resource=resource,
                format_mapping=format_mapping)

            # if format could not be mapped and media_type exists use this value  # noqa
            if (not resource.get('format') and resource.get('media_type')):
                resource['format'] = resource['media_type'].split('/')[-1]

    return pkg_dict


def get_choice_or_fallback(choice, fallback_list, choice_field):
    if choice:
        return choice
    if fallback_list:
        return fallback_list[0].get(choice_field)


def extract_lang_value(value, lang_code):
    new_value = sh.parse_json(value)

    if isinstance(new_value, dict):
        return sh.get_localized_value(
            new_value,
            lang_code,
            default_value=''
        )
    return value


def package_reduce_to_requested_language(pkg_dict, desired_lang_code):
    """# pkg fields"""
    for key, value in pkg_dict.iteritems():
        pkg_dict[key] = extract_lang_value(
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
                    element[field] = extract_lang_value(
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
                pkg_dict['organization'][field] = extract_lang_value(
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
                    element[field] = extract_lang_value(
                        element[field],
                        desired_lang_code
                    )
        except TypeError:
            pass
    return pkg_dict
