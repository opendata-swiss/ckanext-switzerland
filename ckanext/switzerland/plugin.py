import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons
import json
import pprint
import collections
import logging
log = logging.getLogger(__name__)

from ckanext.switzerland import validators
from ckanext.switzerland.logic import (
   ogdch_dataset_count
)
from ckanext.switzerland.helpers import (
   get_dataset_count, get_group_count, get_app_count,
   get_org_count, get_tweet_count, _get_language_value,
   get_localized_org
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
            'list_of_dicts': validators.list_of_dicts,
            }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        facets_dict = collections.OrderedDict()
        facets_dict['groups'] = plugins.toolkit._('Themes')
        facets_dict['tags'] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organization')
        facets_dict['license_id'] = plugins.toolkit._('Terms')
        facets_dict['res_format'] = plugins.toolkit._('Media Type')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        return facets_dict

    # IActions

    def get_actions(self):
        """
        Expose new API methods
        """
        return {
            'ogdch_dataset_count': ogdch_dataset_count,
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
        }


class OgdchLanguagePlugin(plugins.SingletonPlugin):
    def _extract_lang_value(self, value, lang_code):
        new_value = value
        try:
            new_value = json.loads(value)
        except (ValueError, TypeError, AttributeError):
            pass

        if isinstance(new_value, dict):
            return _get_language_value(new_value, lang_code, default_value='')
        return value

    def before_view(self, pkg_dict):
        desired_lang_code = pylons.request.environ['CKAN_LANG']

        # TODO: why is this not already a dict?
        pkg_dict['display_name'] = pkg_dict['title']

        for key, value in pkg_dict.iteritems():
            pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)
        log.debug(pkg_dict)
        return pkg_dict


class OgdchGroupPlugin(OgdchLanguagePlugin):
    plugins.implements(plugins.IGroupController, inherit=True)

    # IGroupController
    def before_view(self, pkg_dict):
        return super(OgdchGroupPlugin, self).before_view(pkg_dict)


class OgdchOrganizationPlugin(OgdchLanguagePlugin):
    plugins.implements(plugins.IOrganizationController, inherit=True)

    # IOrganizationController

    def before_view(self, pkg_dict):
        log.debug("HELL YEAH")
        return super(OgdchOrganizationPlugin, self).before_view(pkg_dict)


class OgdchPackagePlugin(OgdchLanguagePlugin):
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def before_view(self, pkg_dict):
        desired_lang_code = pylons.request.environ['CKAN_LANG']
        # pkg fields
        for key, value in pkg_dict.iteritems():
            pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)

        # groups
        for element in pkg_dict['groups']:
            for field in element:
                element[field] = self._extract_lang_value(element[field], desired_lang_code)

        # resources
        for resource in pkg_dict['resources']:
            if not resource['name'] and resource['title']:
                resource['name'] = resource['title']
            for key, value in resource.iteritems():
                if key not in ['tracking_summary']:
                    resource[key] = self._extract_lang_value(value, desired_lang_code)
        return pkg_dict


    def before_index(self, pkg_dict):
        extract_title = LangToString('title')
        validated_dict = json.loads(pkg_dict['validated_data_dict'])
        
        log.debug(pprint.pformat(validated_dict['title']))

        pkg_dict['res_name'] = map(extract_title, validated_dict[u'resources'])
        pkg_dict['title_string'] = extract_title(validated_dict)
        pkg_dict['description'] = LangToString('description')(validated_dict)

        pkg_dict['title_de'] = validated_dict['title']['de']
        pkg_dict['title_fr'] = validated_dict['title']['fr']
        pkg_dict['title_it'] = validated_dict['title']['it']
        pkg_dict['title_en'] = validated_dict['title']['en']

        log.debug(pprint.pformat(pkg_dict))
        return pkg_dict
   
    def before_search(self, search_params):
        log.debug(pprint.pformat(search_params))
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
