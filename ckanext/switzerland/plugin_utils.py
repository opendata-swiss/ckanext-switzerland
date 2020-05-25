# coding=UTF-8

import os
import re
import json
import logging
import urlparse
import yaml
from collections import OrderedDict
import ckan.plugins.toolkit as toolkit
from ckan.lib.munge import munge_title_to_name
from ckan import logic
from ckan.lib.helpers import lang
from ckanext.switzerland import validators as v
from ckanext.switzerland import logic as l
import ckanext.switzerland.helpers as sh
import ckanext.switzerland.utils as utils

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


def ogdch_get_validators():
    """gets the validators for ogdch plugin"""
    return {
        'multiple_text': v.multiple_text,
        'multiple_text_output': v.multiple_text_output,
        'multilingual_text_output': v.multilingual_text_output,
        'list_of_dicts': v.list_of_dicts,
        'timestamp_to_datetime': v.timestamp_to_datetime,
        'ogdch_language': v.ogdch_language,
        'ogdch_unique_identifier': v.ogdch_unique_identifier,
        'temporals_to_datetime_output': v.temporals_to_datetime_output,
        'parse_json': sh.parse_json,
    }


def ogdch_get_dataset_facets():
    """gets the dataset page facets for ogdch plugin"""
    lang_code = toolkit.request.environ['CKAN_LANG']
    facets_dict = OrderedDict()
    facets_dict['groups'] = toolkit._('Categories')
    facets_dict['keywords_' + lang_code] = toolkit._('Keywords')
    facets_dict['organization'] = toolkit._('Organizations')
    facets_dict['political_level'] = toolkit._('Political levels')
    facets_dict['res_rights'] = toolkit._('Terms of use')
    facets_dict['res_format'] = toolkit._('Formats')
    log.error("OGDCHFACETS {}".format(facets_dict))
    return facets_dict


def ogdch_get_group_facets():
    """gets the group page facets for ogdch plugin"""
    lang_code = toolkit.request.environ['CKAN_LANG']
    facets_dict = OrderedDict()
    facets_dict['keywords_' + lang_code] = toolkit._('Keywords')
    facets_dict['organization'] = toolkit._('Organizations')
    facets_dict['political_level'] = toolkit._('Political levels')
    facets_dict['res_rights'] = toolkit._('Terms of use')
    facets_dict['res_format'] = toolkit._('Formats')
    return facets_dict


def ogdch_get_organization_facets():
    """gets the organization page facets for ogdch plugin"""
    lang_code = toolkit.request.environ['CKAN_LANG']
    facets_dict = OrderedDict()
    facets_dict['groups'] = toolkit._('Categories')
    facets_dict['keywords_' + lang_code] = toolkit._('Keywords')
    facets_dict['res_rights'] = toolkit._('Terms of use')
    facets_dict['res_format'] = toolkit._('Formats')
    return facets_dict


def ogdch_get_actions():
    "gets the actions for ogdch plugin"
    return {
        'ogdch_dataset_count': l.ogdch_dataset_count,
        'ogdch_dataset_terms_of_use': l.ogdch_dataset_terms_of_use,
        'ogdch_dataset_by_identifier': l.ogdch_dataset_by_identifier,
        'ogdch_content_headers': l.ogdch_content_headers,
        'ogdch_autosuggest': l.ogdch_autosuggest,
        'ogdch_cleanup_harvestjobs': l.ogdch_cleanup_harvestjobs,
        'ogdch_shacl_validate': l.ogdch_shacl_validate,
    }


def ogdch_itemplatehelpers_get_helpers():
    """gets the template helpers for ogdch plugin"""
    return {
        'get_dataset_count': sh.get_dataset_count,
        'get_group_count': sh.get_group_count,
        'get_app_count': sh.get_app_count,
        'get_org_count': sh.get_org_count,
        'get_localized_org': sh.get_localized_org,
        'localize_json_title': sh.localize_json_title,
        'get_frequency_name': sh.get_frequency_name,
        'get_political_level': sh.get_political_level,
        'get_terms_of_use_icon': sh.get_terms_of_use_icon,
        'get_dataset_terms_of_use': sh.get_dataset_terms_of_use,
        'get_dataset_by_identifier': sh.get_dataset_by_identifier,
        'get_readable_file_size': sh.get_readable_file_size,
        'get_piwik_config': sh.get_piwik_config,
        'ogdch_localised_number': sh.ogdch_localised_number,
        'ogdch_render_tree': sh.ogdch_render_tree,
        'ogdch_group_tree': sh.ogdch_group_tree,
        'get_showcases_for_dataset': sh.get_showcases_for_dataset,
        'get_terms_of_use_url': sh.get_terms_of_use_url,
        'get_localized_newsletter_url': sh.get_localized_newsletter_url,
    }


def ogdch_ixloader_after_upload(context, dataset_dict, resource_dict):
    # create resource views after a successful upload to the DataStore
    toolkit.get_action('resource_create_default_resource_views')(
        context,
        {
            'resource': resource_dict,
            'package': dataset_dict,
        }
    )


def ogdch_base_iconfigurer_get_mapping():
    """gets the format mapping from  a file for ogdch controller plugins"""
    try:
        mapping_path = os.path.join(__location__, 'mapping.yaml')
        with open(mapping_path, 'r') as format_mapping_file:
            format_mapping = yaml.safe_load(format_mapping_file)
    except (IOError, yaml.YAMLError) as exception:
        raise utils.FormatMappingNotLoadedError(
            'Loading Format-Mapping from Path: (%s) '
            'failed with Exception: (%s)'
            % (mapping_path, exception)
        )
    else:
        return format_mapping



def ogdch_modify_pkg_for_web(pkg_dict, format_mapping):
    """for website views of the dataset"""
    pkg_dict = package_map_ckan_default_fields(pkg_dict)

    # prepare format of resources
    pkg_dict = utils.prepare_resources_format(
        pkg_dict=pkg_dict,
        format_mapping=format_mapping)

    # replace langauge dicts with requested language strings
    desired_lang_code = utils.get_request_language()
    pkg_dict = utils.package_reduce_to_requested_language(
        pkg_dict, desired_lang_code
    )
    return pkg_dict



def ogdch_modify_pkg_for_api(pkg_dict):
    """for api views of the dataset since
    before_view is not called in this case"""
    pkg_dict = package_map_ckan_default_fields(pkg_dict)
    # render groups as json
    groups = pkg_dict.get('groups')
    for group in groups:
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


def ogdch_pkg_ipackagecontroller_before_index(search_data, format_mapping):
    """prepare the package data for search for the ogdch package controller plugin"""
    if (search_data.get('type') != 'dataset'):
        return search_data
    validated_dict = json.loads(search_data['validated_data_dict'])
    search_data['res_name'] = [utils.lang_to_string(r, 'title') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_en'] = [sh.get_localized_value(r['title'], 'en') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_de'] = [sh.get_localized_value(r['title'], 'de') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_fr'] = [sh.get_localized_value(r['title'], 'fr') for r in validated_dict[u'resources']]  # noqa
    search_data['res_name_it'] = [sh.get_localized_value(r['title'], 'it') for r in validated_dict[u'resources']]  # noqa
    search_data['res_description_en'] = [sh.get_localized_value(r['description'], 'en') for r in
                                         validated_dict[u'resources']]  # noqa
    search_data['res_description_de'] = [sh.get_localized_value(r['description'], 'de') for r in
                                         validated_dict[u'resources']]  # noqa
    search_data['res_description_fr'] = [sh.get_localized_value(r['description'], 'fr') for r in
                                         validated_dict[u'resources']]  # noqa
    search_data['res_description_it'] = [sh.get_localized_value(r['description'], 'it') for r in
                                         validated_dict[u'resources']]  # noqa
    search_data['groups_en'] = [sh.get_localized_value(g['display_name'], 'en') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_de'] = [sh.get_localized_value(g['display_name'], 'de') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_fr'] = [sh.get_localized_value(g['display_name'], 'fr') for g in validated_dict[u'groups']]  # noqa
    search_data['groups_it'] = [sh.get_localized_value(g['display_name'], 'it') for g in validated_dict[u'groups']]  # noqa
    search_data['res_description'] = [utils.lang_to_string('description')(r) for r in
                                      validated_dict[u'resources']]  # noqa
    search_data['res_format'] = utils.prepare_formats_for_index(
        resources=validated_dict[u'resources'], format_mapping=format_mapping)
    search_data['res_rights'] = [sh.simplify_terms_of_use(r['rights']) for r in validated_dict[u'resources'] if
                                 'rights' in r.keys()]  # noqa
    search_data['title_string'] = utils.lang_to_string(validated_dict, 'title')
    search_data['description'] = utils.lang_to_string(validated_dict, 'description')  # noqa
    if 'political_level' in validated_dict[u'organization']:
        search_data['political_level'] = validated_dict[u'organization'][u'political_level']  # noqa

    search_data['identifier'] = validated_dict.get('identifier')
    search_data['contact_points'] = [c['name'] for c in validated_dict.get('contact_points', [])]  # noqa
    search_data['publishers'] = [p['label'] for p in validated_dict.get('publishers', [])]  # noqa

    search_data['see_alsos'] = [d.get('dataset_identifier', d) for d in validated_dict.get('see_alsos', [])]  # noqa
    search_data['metadata_created'] = search_data.get('metadata_created', '')
    search_data['metadata_modified'] = search_data.get('metadata_modified', '')
    for lang_code in sh.get_langs():
        search_data['title_' + lang_code] = sh.get_localized_value(
            validated_dict.get('title'),
            lang_code
        )
        search_data['title_string_' + lang_code] = munge_title_to_name(
            sh.get_localized_value(validated_dict.get('title'), lang_code)
        )
        search_data['description_' + lang_code] = sh.get_localized_value(  # noqa
            validated_dict.get('description'),
            lang_code
        )
        search_data['keywords_' + lang_code] = sh.get_localized_value(
            validated_dict.get('keywords'),
            lang_code
        )
        search_data['organization_' + lang_code] = sh.get_localized_value(  # noqa
            validated_dict.get('organization').get('title'),
            lang_code
        )
    search_data = utils.prepare_suggest_context(
        search_data,
        validated_dict
    )
    return search_data


def ogdch_pkg_ipackagecontroller_before_search(search_params):
    '''
    # borrowed from ckanext-multilingual (core extension)
    search in correct language-specific field and boost
    results in current language
    '''
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

    # Unless the query is already being filtered by any type
    # (either positively, or negatively), reduce to only display
    # 'dataset' type
    # This is done because by standard all types are displayed, this
    # leads to strange situations where e.g. harvest sources are shown
    # on organization pages.
    # TODO: fix issue https://github.com/ckan/ckan/issues/2803 in CKAN core
    fq = search_params.get('fq', '')
    if 'dataset_type:' not in fq:
        search_params.update({'fq': "%s +dataset_type:dataset" % fq})

    # remove colon followed by a space from q to avoid false negatives
    q = search_params.get('q', '')
    search_params['q'] = re.sub(":\s", " ", q)

    return search_params


def ogdch_reduce_simple_ckandict_to_one_language(ckan_dict):
    req_lang = lang()
    grp_localized_dict = {}
    for k,v in ckan_dict.items():
        grp_localized_dict[k] = utils.extract_lang_value(v, req_lang)
    return grp_localized_dict


def ogdch_set_resource_format(resource, format_mapping):
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


def package_map_ckan_default_fields(pkg_dict):
    pkg_dict['display_name'] = pkg_dict.get('title')
    pkg_dict['maintainer'] = utils.get_choice_or_fallback(
        choice=pkg_dict.get('maintainer'),
        fallback_list=pkg_dict.get('contact_points'),
        choice_field='name'
    )
    pkg_dict['maintainer_email'] = utils.get_choice_or_fallback(
        choice=pkg_dict.get('maintainer_email'),
        fallback_list=pkg_dict.get('contact_points'),
        choice_field='email'
    )
    pkg_dict['author'] = utils.get_choice_or_fallback(
        choice=pkg_dict.get('maintainer_email'),
        fallback_list=pkg_dict.get('publishers'),
        choice_field='label'
    )
    if pkg_dict.get('resources') is not None:
        for resource in pkg_dict['resources']:
            resource['name'] = resource['title']
    return pkg_dict
