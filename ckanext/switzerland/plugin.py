# coding=UTF-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import pylons
import json
import re
import pprint
import collections
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers import paginate
import logging
log = logging.getLogger(__name__)

from ckanext.switzerland import validators
from ckanext.switzerland.logic import (
   ogdch_dataset_count, ogdch_dataset_terms_of_use,
   ogdch_dataset_by_identifier, ogdch_content_headers
)
from ckanext.switzerland.helpers import (
   get_dataset_count, get_group_count, get_app_count,
   get_org_count, get_tweet_count, get_localized_value,
   get_localized_org, get_localized_pkg, localize_json_title,
   get_frequency_name, get_terms_of_use_icon, get_dataset_terms_of_use,
   get_dataset_by_identifier, get_readable_file_size,
   simplify_terms_of_use, parse_json, get_piwik_config
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
            'ogdch_unique_identifier': validators.ogdch_unique_identifier,
            'temporals_to_datetime_output': validators.temporals_to_datetime_output,
            'parse_json': parse_json,
        }

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        lang_code = pylons.request.environ['CKAN_LANG']
        facets_dict = collections.OrderedDict()
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        lang_code = pylons.request.environ['CKAN_LANG']
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')

    def organization_facets(self, facets_dict, organization_type, package_type):
        lang_code = pylons.request.environ['CKAN_LANG']
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')

    # IActions

    def get_actions(self):
        """
        Expose new API methods
        """
        return {
            'ogdch_dataset_count': ogdch_dataset_count,
            'ogdch_dataset_terms_of_use': ogdch_dataset_terms_of_use,
            'ogdch_dataset_by_identifier': ogdch_dataset_by_identifier,
            'ogdch_content_headers': ogdch_content_headers,
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
            'get_piwik_config': get_piwik_config,
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
            return pkg_dict

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

    def is_supported_package_type(self, pkg_dict):
        # only package type 'dataset' is supported (not harvesters!)
        try:
            return (pkg_dict['type'] == 'dataset')
        except KeyError:
            return False

    # IPackageController

    def before_view(self, pkg_dict):
        if not self.is_supported_package_type(pkg_dict):
            return pkg_dict

        try:
            desired_lang_code = pylons.request.environ['CKAN_LANG']
        except TypeError:
            desired_lang_code = pylons.config.get('ckan.locale_default', 'en')

        # pkg fields
        for key, value in pkg_dict.iteritems():
            pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)

        # groups
        try:
            for element in pkg_dict['groups']:
                for field in element:
                    element[field] = self._extract_lang_value(element[field], desired_lang_code)
        except TypeError:
            pass

        # organization
        try:
            for field in pkg_dict['organization']:
                pkg_dict['organization'][field] = self._extract_lang_value(pkg_dict['organization'][field], desired_lang_code)
        except TypeError:
            pass

        return pkg_dict

    def after_show(self, context, pkg_dict):
        if not self.is_supported_package_type(pkg_dict):
            return

        # groups
        if pkg_dict['groups'] is not None:
            for group in pkg_dict['groups']:
                # TODO: somehow the title is messed up here, but the display_name is okay
                group['title'] = group['display_name']
                for field in group:
                    group[field] = parse_json(group[field])

        # organization
        if pkg_dict['organization'] is not None:
            for field in pkg_dict['organization']:
                pkg_dict['organization'][field] = parse_json(pkg_dict['organization'][field])

    def before_index(self, pkg_dict):
        if not self.is_supported_package_type(pkg_dict):
            return pkg_dict

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

# Monkeypatch to style CKAN pagination
class OGDPage(paginate.Page):
    # Curry the pager method of the webhelpers.paginate.Page class, so we have
    # our custom layout set as default.

    def pager(self, *args, **kwargs):
        kwargs.update(
            format=u"<ul class='pagination'>$link_previous ~2~ $link_next</ul>",
            symbol_previous=u'«', symbol_next=u'»',
            curpage_attr={'class': 'active'}, link_attr={}
        )
        return super(OGDPage, self).pager(*args, **kwargs)

    # Put each page link into a <li> (for Bootstrap to style it)

    def _pagerlink(self, page, text, extra_attributes=None):
        anchor = super(OGDPage, self)._pagerlink(page, text)
        extra_attributes = extra_attributes or {}
        return HTML.li(anchor, **extra_attributes)

    # Change 'current page' link from <span> to <li><a>
    # and '..' into '<li><a>..'
    # (for Bootstrap to style them properly)

    def _range(self, regexp_match):
        html = super(OGDPage, self)._range(regexp_match)
        # Convert ..
        dotdot = '<span class="pager_dotdot">..</span>'
        dotdot_link = HTML.li(HTML.a('...', href='#'), class_='disabled')
        html = re.sub(dotdot, dotdot_link, html)

        # Convert current page
        text = '%s' % self.page
        current_page_span = str(HTML.span(c=text, **self.curpage_attr))
        current_page_link = self._pagerlink(self.page, text,
                                            extra_attributes=self.curpage_attr)
        return re.sub(current_page_span, current_page_link, html)

h.Page = OGDPage