import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import pylons
import json
import pprint
import collections
import logging
log = logging.getLogger(__name__)

from ckanext.switzerland import validators
from ckanext.switzerland.logic import (
   ogdch_dataset_count, ogdch_dataset_terms_of_use,
   ogdch_dataset_by_identifier
)
from ckanext.switzerland.helpers import (
   get_dataset_count, get_group_count, get_app_count,
   get_org_count, get_tweet_count, get_localized_value,
   get_localized_org, get_localized_pkg, localize_json_title,
   get_frequency_name, get_terms_of_use_icon, get_dataset_terms_of_use,
   get_dataset_by_identifier, get_readable_file_size,
   simplify_terms_of_use, parse_json
)



class OgdchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'switzerland')

    # IValidators

    def get_validators(self):
        return {
            'multiple_text': validators.multiple_text,
            'multiple_text_output': validators.multiple_text_output,
            'multilingual_text_output': validators.multilingual_text_output,
            'list_of_dicts': validators.list_of_dicts,
            'timestamp_to_datetime': validators.timestamp_to_datetime,
            'ogdch_multiple_choice': validators.ogdch_multiple_choice,
            'temporals_to_datetime_output': validators.temporals_to_datetime_output,
            'parse_json': parse_json,
        }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        lang_code = pylons.request.environ['CKAN_LANG']
        facets_dict = collections.OrderedDict()
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organization')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Media Type')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        lang_code = pylons.request.environ['CKAN_LANG']
        facets_dict = collections.OrderedDict()
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organization')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Media Type')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        lang_code = pylons.request.environ['CKAN_LANG']
        facets_dict = collections.OrderedDict()
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Media Type')
        return facets_dict

    # IActions

    def get_actions(self):
        """
        Expose new API methods
        """
        return {
            'ogdch_dataset_count': ogdch_dataset_count,
            'ogdch_dataset_terms_of_use': ogdch_dataset_terms_of_use,
            'ogdch_dataset_by_identifier': ogdch_dataset_by_identifier,
        }

    # ITemplateHelpers

    def get_helpers(self):
        """
        Provide template helper functions
        """
        return {
            'get_dataset_count': get_dataset_count,
            'get_group_count': get_group_count,
            'get_app_count': get_app_count,
            'get_org_count': get_org_count,
            'get_tweet_count': get_tweet_count,
            'get_localized_org': get_localized_org,
            'get_localized_pkg': get_localized_pkg,
            'localize_json_title': localize_json_title,
            'get_frequency_name': get_frequency_name,
            'get_terms_of_use_icon': get_terms_of_use_icon,
            'get_dataset_terms_of_use': get_dataset_terms_of_use,
            'get_dataset_by_identifier': get_dataset_by_identifier,
            'get_readable_file_size': get_readable_file_size,
        }


class OgdchLanguagePlugin(plugins.SingletonPlugin):
    def _extract_lang_value(self, value, lang_code):
        new_value = parse_json(value)

        if isinstance(new_value, dict):
            return get_localized_value(new_value, lang_code, default_value='')
        return value

    def before_view(self, pkg_dict):
        # try to parse all values as JSON
        for key, value in pkg_dict.iteritems():
            pkg_dict[key] = parse_json(value)

        # read pylons values if available
        try:
            path = pylons.request.path
            desired_lang_code = pylons.request.environ['CKAN_LANG']
        except TypeError:
            path = ''
            desired_lang_code = pylons.config.get('ckan.locale_default', 'en')

        # Do not change the resulting dict for API requests
        if path.startswith('/api'):
            return pkg_dict

        pkg_dict['display_name'] = pkg_dict['title']
        for key, value in pkg_dict.iteritems():
            if not self._ignore_field(key):
                pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)
        return pkg_dict

    def _ignore_field(self, key):
        return False


class OgdchGroupPlugin(OgdchLanguagePlugin):
    plugins.implements(plugins.IGroupController, inherit=True)

    # IGroupController
    def before_view(self, pkg_dict):
        return super(OgdchGroupPlugin, self).before_view(pkg_dict)


class OgdchOrganizationPlugin(OgdchLanguagePlugin):
    plugins.implements(plugins.IOrganizationController, inherit=True)

    # IOrganizationController

    def before_view(self, pkg_dict):
        return super(OgdchOrganizationPlugin, self).before_view(pkg_dict)

class OgdchResourcePlugin(OgdchLanguagePlugin):
    plugins.implements(plugins.IResourceController, inherit=True)
    
    # IResourceController

    def before_show(self, pkg_dict):
        return super(OgdchResourcePlugin, self).before_view(pkg_dict)

    def _ignore_field(self, key):
        return key == 'tracking_summary'


class OgdchPackagePlugin(OgdchLanguagePlugin):
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def before_view(self, pkg_dict):
        try:
            desired_lang_code = pylons.request.environ['CKAN_LANG']
        except TypeError:
            desired_lang_code = pylons.config.get('ckan.locale_default', 'en')

        # pkg fields
        for key, value in pkg_dict.iteritems():
            pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)

        # groups
        for element in pkg_dict['groups']:
            for field in element:
                element[field] = self._extract_lang_value(element[field], desired_lang_code)

        # organization
        for field in pkg_dict['organization']:
            pkg_dict['organization'][field] = self._extract_lang_value(pkg_dict['organization'][field], desired_lang_code)

        return pkg_dict

    def after_show(self, context, pkg_dict):
        # TODO: somehow the title is messed up here, but the display_name is okay
        for group in pkg_dict['groups']:
            group['title'] = group['display_name']

    def before_index(self, pkg_dict):
        extract_title = LangToString('title')
        validated_dict = json.loads(pkg_dict['validated_data_dict'])
        
        # log.debug(pprint.pformat(validated_dict))

        pkg_dict['res_name'] = [r['title'] for r in validated_dict[u'resources']]
        pkg_dict['res_format'] = [r['media_type'] for r in validated_dict[u'resources']]
        pkg_dict['res_rights'] = [simplify_terms_of_use(r['rights']) for r in validated_dict[u'resources']]
        pkg_dict['title_string'] = extract_title(validated_dict)
        pkg_dict['description'] = LangToString('description')(validated_dict)

        try:
            pkg_dict['title_de'] = validated_dict['title']['de']
            pkg_dict['title_fr'] = validated_dict['title']['fr']
            pkg_dict['title_it'] = validated_dict['title']['it']
            pkg_dict['title_en'] = validated_dict['title']['en']

            pkg_dict['keywords_de'] = validated_dict['keywords']['de']
            pkg_dict['keywords_fr'] = validated_dict['keywords']['fr']
            pkg_dict['keywords_it'] = validated_dict['keywords']['it']
            pkg_dict['keywords_en'] = validated_dict['keywords']['en']
        except KeyError:
            pass

        # log.debug(pprint.pformat(pkg_dict))
        return pkg_dict
   
    def before_search(self, search_params):
        # log.debug(pprint.pformat(search_params))
        return search_params


class LangToString(object):
    def __init__(self, attribute):
        self.attribute = attribute

    def __call__(self, data_dict):
        lang = data_dict[self.attribute]
        return (
            '%s - %s - %s - %s'
            % (lang['de'], lang['fr'], lang['it'], lang['en'])
        )
