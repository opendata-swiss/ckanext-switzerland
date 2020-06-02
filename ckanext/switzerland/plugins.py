# coding=UTF-8

from ckanext.switzerland import validators as v
from ckanext.switzerland import logic as l
import ckanext.switzerland.helpers as sh
import ckanext.switzerland.plugin_utils as pu
import re
from webhelpers.html import HTML
from webhelpers import paginate
import ckan.plugins as plugins
from ckan.lib.plugins import DefaultTranslation
import ckanext.xloader.interfaces as ix
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import collections
import os
import logging
log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


class OgdchPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)

    # ITranslation

    def i18n_domain(self):
        return 'ckanext-switzerland'

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    # IValidators

    def get_validators(self):
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

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
        facets_dict = collections.OrderedDict()
        facets_dict['groups'] = plugins.toolkit._('Categories')
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['political_level'] = plugins.toolkit._('Political levels')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
        # the IFacets implementation of CKAN 2.4 is broken,
        # clear the dict instead and change the passed in argument
        facets_dict.clear()
        facets_dict['keywords_' + lang_code] = plugins.toolkit._('Keywords')
        facets_dict['organization'] = plugins.toolkit._('Organizations')
        facets_dict['political_level'] = plugins.toolkit._('Political levels')
        facets_dict['res_rights'] = plugins.toolkit._('Terms of use')
        facets_dict['res_format'] = plugins.toolkit._('Formats')

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        lang_code = toolkit.request.environ['CKAN_LANG']
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
            'ogdch_dataset_count': l.ogdch_dataset_count,
            'ogdch_dataset_terms_of_use': l.ogdch_dataset_terms_of_use,
            'ogdch_dataset_by_identifier': l.ogdch_dataset_by_identifier,
            'ogdch_content_headers': l.ogdch_content_headers,
            'ogdch_autosuggest': l.ogdch_autosuggest,
        }

    # ITemplateHelpers

    def get_helpers(self):
        """
        Provide template helper functions
        """
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


class OgdchMixin(object):
    """
    gets format mapping
    """
    def update_config(self, config):
        self.format_mapping = \
            pu.ogdch_get_format_mapping()


class OgdchGroupPlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IGroupController, inherit=True)

    def before_view(self, pkg_dict):
        pkg_dict = pu._prepare_package_json(
            pkg_dict=pkg_dict,
            format_mapping=self.format_mapping,
            ignore_fields=[]
        )
        return pkg_dict


class OgdchOrganizationPlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IOrganizationController, inherit=True)

    def before_view(self, pkg_dict):
        pkg_dict = pu._prepare_package_json(
            pkg_dict=pkg_dict,
            format_mapping=self.format_mapping,
            ignore_fields=[]
        )
        return pkg_dict


class OgdchResourcePlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IResourceController
    def before_show(self, res_dict):
        pu.ogdch_prepare_res_dict_before_show(
            res_dict=res_dict,
            format_mapping=self.format_mapping,
            ignore_fields=['tracking_summary']
        )


class OgdchPackagePlugin(plugins.SingletonPlugin, OgdchMixin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(ix.IXloader, inherit=True)

    # IRouter

    def before_map(self, map):
        """create perma-link route"""
        map.connect('perma_redirect', '/perma/{id}',
                    controller='ckanext.switzerland.controller:OgdchPermaController',  # noqa
                    action='read')
        return map

    # IPackageController

    def before_view(self, pkg_dict):
        """transform pkg dict before view"""
        pkg_dict = pu._prepare_package_json(
            pkg_dict=pkg_dict,
            format_mapping=self.format_mapping,
            ignore_fields=[]
        )
        return pkg_dict

    def after_show(self, context, pkg_dict):
        """
        before_view isn't called in API requests -> after_show is
        BUT (!) after_show is also called when packages get indexed
        and there we need all languages.
        -> find a solution to _prepare_package_json() in an API call.
        """
        pkg_dict = pu.ogdch_prepare_pkg_dict_for_api(pkg_dict)
        return pkg_dict

    def before_index(self, search_data):
        """
        Search data before index
        """
        search_data = pu.ogdch_prepare_search_data_for_index(
            search_data=search_data,
            format_mapping=self.format_mapping
        )
        return search_data

    def before_search(self, search_params):
        """
        Adjust search parameters
        """
        search_params = pu.ogdch_adjust_search_params(search_params)
        return search_params

    # IXloader

    def after_upload(self, context, resource_dict, dataset_dict):
        # create resource views after a successful upload to the DataStore
        toolkit.get_action('resource_create_default_resource_views')(
            context,
            {
                'resource': resource_dict,
                'package': dataset_dict,
            }
        )


class OgdchOrganisationSearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)

    # IRouter
    # Redirect organization_read /organization/{id} to custom controller
    # fix the search on the org page and use Hierarchy if needed

    def before_map(self, map):
        map.connect('organization_read', '/organization/{id}',
                    controller='ckanext.switzerland.controller:OgdchOrganizationSearchController',  # noqa
                    action='read')
        map.connect('organization_index', '/organization',
                    controller='ckanext.switzerland.controller:OgdchOrganizationSearchController',  # noqa
                    action='index')
        return map


class OgdchGroupSearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)

    # IRouter
    # Redirect gourp_read /group/{id} to custom controller
    # fix the search on the group page if search term and facets are combined

    def before_map(self, map):
        map.connect('group_read', '/group/{id}',
                    controller='ckanext.switzerland.controller:OgdchGroupSearchController',  # noqa
                    action='read')
        return map


# Monkeypatch to style CKAN pagination
class OGDPage(paginate.Page):
    # Curry the pager method of the webhelpers.paginate.Page class, so we have
    # our custom layout set as default.

    def pager(self, *args, **kwargs):
        kwargs.update(
            format=u"<ul class='pagination'>$link_previous ~2~ $link_next</ul>",  # noqa
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
