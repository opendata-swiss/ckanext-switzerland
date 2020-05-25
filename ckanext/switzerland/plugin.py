# coding=UTF-8

import ckan.plugins as plugins
from ckan.lib.plugins import DefaultTranslation
import ckanext.xloader.interfaces as ix
import ckan.plugins.toolkit as toolkit
import os
import logging
import ckanext.switzerland.plugin_utils as pu
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
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(ix.IXloader, inherit=True)

    # ------------------------------------------------------------
    # ITranslation
    # ------------------------------------------------------------
    # Allows extensions to provide their own translation strings.

    def i18n_domain(self):
        u'''Change the gettext domain handled by this plugin'''
        gettext_domain =  'ckanext-switzerland'
        log.debug("ITranslation i18n_domain: OUT {}".format(gettext_domain))
        return gettext_domain

    # ------------------------------------------------------------
    # IConfigurer
    # ------------------------------------------------------------
    # Configure CKAN environment via the ``config`` object

    def update_config(self, config_):
        u'''
        Return a schema with the runtime-editable config options

        CKAN will use the returned schema to decide which configuration options
        can be edited during runtime (using
        :py:func:`ckan.logic.action.update.config_option_update`) and to
        validate them before storing them.

        Defaults to
        :py:func:`ckan.logic.schema.default_update_configuration_schema`, which
        will be passed to all extensions implementing this method, which can
        add or remove runtime-editable config options to it.

        :param schema: a dictionary mapping runtime-editable configuration
          option keys to lists
          of validator and converter functions to be applied to those keys
        :type schema: dictionary

        :returns: a dictionary mapping runtime-editable configuration option
          keys to lists of
          validator and converter functions to be applied to those keys
        :rtype: dictionary
        '''
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        log.debug("IConfigurer: added templates and public to the configuration")

    # ------------------------------------------------------------
    # IValidators
    # ------------------------------------------------------------
    # Add extra validators to be returned by
    #     :py:func:`ckan.plugins.toolkit.get_validator`.

    def get_validators(self):
        u'''Return the validator functions provided by this plugin.

        Return a dictionary mapping validator names (strings) to
        validator functions. For example::

            {'valid_shoe_size': shoe_size_validator,
             'valid_hair_color': hair_color_validator}

        These validator functions would then be available when a
        plugin calls :py:func:`ckan.plugins.toolkit.get_validator`.
        '''
        validators = pu.ogdch_get_validators()
        log.debug("IValidators: get validators OUT {}".format(validators))
        return validators

    # ------------------------------------------------------------
    # IFacets
    # ------------------------------------------------------------
    # Customize the search facets shown on search pages.

    def dataset_facets(self, facets_dict, package_type):
        u'''Modify and return the ``facets_dict`` for the dataset search page.

        The ``package_type`` is the type of package that these facets apply to.
        Plugins can provide different search facets for different types of
        package. See :py:class:`~ckan.plugins.interfaces.IDatasetForm`.

        :param facets_dict: the search facets as currently specified
        :type facets_dict: OrderedDict

        :param package_type: the package type that these facets apply to
        :type package_type: string

        :returns: the updated ``facets_dict``
        :rtype: OrderedDict

        '''
        dataset_facets = pu.ogdch_get_dataset_facets()
        log.debug("IFacets: get dataset facets OUT {}".format(dataset_facets))
        return dataset_facets

    def group_facets(self, facets_dict, group_type, package_type):
        u'''Modify and return the ``facets_dict`` for a group's page.

        The ``package_type`` is the type of package that these facets apply to.
        Plugins can provide different search facets for different types of
        package. See :py:class:`~ckan.plugins.interfaces.IDatasetForm`.

        The ``group_type`` is the type of group that these facets apply to.
        Plugins can provide different search facets for different types of
        group. See :py:class:`~ckan.plugins.interfaces.IGroupForm`.

        :param facets_dict: the search facets as currently specified
        :type facets_dict: OrderedDict

        :param group_type: the group type that these facets apply to
        :type group_type: string

        :param package_type: the package type that these facets apply to
        :type package_type: string

        :returns: the updated ``facets_dict``
        :rtype: OrderedDict

        '''
        group_facets = pu.ogdch_get_group_facets()
        log.error("OGDCHSPY IFacets: get group facets OUT {}".format(group_facets))
        return group_facets

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        u'''Modify and return the ``facets_dict`` for an organization's page.

        The ``package_type`` is the type of package that these facets apply to.
        Plugins can provide different search facets for different types of
        package. See :py:class:`~ckan.plugins.interfaces.IDatasetForm`.

        The ``organization_type`` is the type of organization that these facets
        apply to.  Plugins can provide different search facets for different
        types of organization. See
        :py:class:`~ckan.plugins.interfaces.IGroupForm`.

        :param facets_dict: the search facets as currently specified
        :type facets_dict: OrderedDict

        :param organization_type: the organization type that these facets apply
                                  to
        :type organization_type: string

        :param package_type: the package type that these facets apply to
        :type package_type: string

        :returns: the updated ``facets_dict``
        :rtype: OrderedDict

        '''
        organization_facets = pu.ogdch_get_organization_facets()
        log.debug("IFacets: get organization facets OUT {}".format(organization_facets))
        return organization_facets

    # ------------------------------------------------------------
    # IActions
    # ------------------------------------------------------------
    # Allow adding of actions to the logic layer

    def get_actions(self):
        u'''
        Should return a dict, the keys being the name of the logic
        function and the values being the functions themselves.

        By decorating a function with the `ckan.logic.side_effect_free`
        decorator, the associated action will be made available by a GET
        request (as well as the usual POST request) through the action API.

        By decrorating a function with the 'ckan.plugins.toolkit.chained_action,
        the action will be chained to another function defined in plugins with a
        "first plugin wins" pattern, which means the first plugin declaring a
        chained action should be called first. Chained actions must be
        defined as action_function(original_action, context, data_dict)
        where the first parameter will be set to the action function in
        the next plugin or in core ckan. The chained action may call the
        original_action function, optionally passing different values,
        handling exceptions, returning different values and/or raising
        different exceptions to the caller.
        '''
        actions = pu.ogdch_get_actions()
        log.debug("IActionss: get actions OUT {}".format(actions))
        return actions

    # ------------------------------------------------------------
    # ITemplateHelpers
    # ------------------------------------------------------------
    # Add custom template helper functions.

    def get_helpers(self):
        u'''Return a dict mapping names to helper functions.

        The keys of the dict should be the names with which the helper
        functions will be made available to templates, and the values should be
        the functions themselves. For example, a dict like:
        ``{'example_helper': example_helper}`` allows templates to access the
        ``example_helper`` function via ``h.example_helper()``.

        Function names should start with the name of the extension providing
        the function, to prevent name clashes between extensions.

        '''
        helpers = pu.ogdch_itemplatehelpers_get_helpers()
        log.debug("TemplateHelpers: get template helpers OUT {}".format(helpers))
        return helpers

    # ------------------------------------------------------------
    # IXloader
    # ------------------------------------------------------------
    # The IXloader interface allows plugin authors to receive notifications
    # before and after a resource is submitted to the xloader service, as
    # well as determining whether a resource should be submitted in can_upload

    def after_upload(self, context, resource_dict, dataset_dict):
        """ After a resource has been successfully upload to the datastore
        this method will be called with the resource dictionary and the
        package dictionary for this resource.

        :param context: The context within which the upload happened
        :param resource_dict: The dict represenstaion of the resource that was
            successfully uploaded to the datastore
        :param dataset_dict: The dict represenstation of the dataset containing
            the resource that was uploaded
        """
        log.debug("IXloader: create views for DATASET {} RESOURCE {}"
                 .format(resource_dict, dataset_dict))
        pu.ogdch_ixloader_after_upload(
            context=context,
            resource_dict=resource_dict,
            dataset_dict=dataset_dict)

    # ------------------------------------------------------------
    # IRouter
    # ------------------------------------------------------------
    # Add custom template helper functions.
    # create perma-link route
    def before_map(self, map):
        map.connect('perma_redirect', '/perma/{id}',
                    controller='ckanext.switzerland.controller:OgdchPermaController',  # noqa
                    action='read')
        map.connect('organization_read', '/organization/{id}',
                    controller='ckanext.switzerland.controller:OgdchOrganizationSearchController',  # noqa
                    action='read')
        map.connect('organization_index', '/organization',
                    controller='ckanext.switzerland.controller:OgdchOrganizationSearchController',  # noqa
                    action='index')
        map.connect('group_read', '/group/{id}',
                    controller='ckanext.switzerland.controller:OgdchGroupSearchController',  # noqa
                    action='read')
        return map



class OgdchBaseControllerPlugin(plugins.SingletonPlugin):
    """
    Base Plugin for Controllers Plugins:
    IPackageController, IGroupController and IOrganizationController
    need to be implemented in different plugins
    """
    plugins.implements(plugins.IConfigurer)

    # ------------------------------------------------------------
    # IConfigurer
    # ------------------------------------------------------------
    # Configure CKAN environment via the ``config`` object

    def update_config(self, config_):
        u'''
        Return a schema with the runtime-editable config options

        CKAN will use the returned schema to decide which configuration options
        can be edited during runtime (using
        :py:func:`ckan.logic.action.update.config_option_update`) and to
        validate them before storing them.

        Defaults to
        :py:func:`ckan.logic.schema.default_update_configuration_schema`, which
        will be passed to all extensions implementing this method, which can
        add or remove runtime-editable config options to it.

        :param schema: a dictionary mapping runtime-editable configuration
          option keys to lists
          of validator and converter functions to be applied to those keys
        :type schema: dictionary

        :returns: a dictionary mapping runtime-editable configuration option
          keys to lists of
          validator and converter functions to be applied to those keys
        :rtype: dictionary
        '''
        self.format_mapping = \
            pu.ogdch_base_iconfigurer_get_mapping()
        log.debug("IConfigurer: format mapping: {}".format(self.format_mapping))


class OgdchPackageControllerPlugin(OgdchBaseControllerPlugin):
    """
    implements IPackageController
    """
    plugins.implements(plugins.IPackageController, inherit=True)

    # ------------------------------------------------------------
    # IPackageController
    # ------------------------------------------------------------
    # Hook into the package controller.

    def before_view(self, pkg_dict):
        u'''
        this method is used before datasets are displayed on the website
        '''
        if (pkg_dict.get('type') == 'dataset'):
            log.debug("OGDCHSPY before view transform done")
            pkg_dict = pu.ogdch_modify_pkg_for_web(
                pkg_dict=pkg_dict, format_mapping=self.format_mapping)
            log.error("OGDCHSPY IPackageController before-view: pkg_dict OUT {}"
                     .format(pkg_dict))
        return pkg_dict

    def after_show(self, context, pkg_dict):
        u'''
        this method is used before all request on datasets:
        also api request, or requests with an extension of:
         .ttl, .jsonld, .n3, .rdf, .xml
        '''
        log.debug("OGDCHSPY in package controller after show")
        path = toolkit.request.path
        if any([
            path.startswith('/api'),
            path.endswith('.xml'),
            path.endswith('.rdf'),
            path.endswith('.n3'),
            path.endswith('.ttl'),
            path.endswith('.jsonld')]):
            log.error("OGDCHSPY after show transform done")
            pkg_dict = pu.ogdch_modify_pkg_for_api(pkg_dict=pkg_dict)
        return pkg_dict

    def before_search(self, search_params):
        u'''
        Extensions will receive a dictionary with the query parameters,
        and should return a modified (or not) version of it.

        search_params will include an `extras` dictionary with all values
        from fields starting with `ext_`, so extensions can receive user
        input from specific fields.
        '''
        search_params = pu.ogdch_pkg_ipackagecontroller_before_search(
            search_params=search_params)
        log.debug("search params before search {}".format(search_params))
        return search_params

    def before_index(self, pkg_dict):
        u'''
        Extensions will receive what will be given to the solr for
        indexing. This is essentially a flattened dict (except for
        multli-valued fields such as tags) of all the terms sent to
        the indexer. The extension can modify this by returning an
        altered version.
        '''
        if (pkg_dict.get('type') == 'dataset'):
            pkg_dict = pu.ogdch_pkg_ipackagecontroller_before_index(
                search_data=pkg_dict,
                format_mapping=self.format_mapping)
            log.debug("pkg_dict before index {}".format(pkg_dict))
        return pkg_dict


class OgdchGroupControllerPlugin(OgdchBaseControllerPlugin):
    plugins.implements(plugins.IGroupController, inherit=True)
    def before_view(self, grp_dict):
        """The group controller needs to do the same as the package controller"""
        log.error("IGroupController group before_view: IN {}".format(grp_dict))
        grp_dict = pu.ogdch_reduce_simple_ckandict_to_one_language(grp_dict)
        log.error("IGroupController group before_view: grp_dict {}".format(grp_dict))
        return grp_dict


class OgdchOrganizationControllerPlugin(OgdchBaseControllerPlugin):
    plugins.implements(plugins.IOrganizationController, inherit=True)

    # IOrganizationController
    def before_view(self, org_dict):
        """The organization controller needs to do the same as the package controller"""
        log.debug("IOrganizationController organization before_view: org_dict {}".format(org_dict))
        org_dict = pu.ogdch_reduce_simple_ckandict_to_one_language(org_dict)
        return org_dict


class OgdchResourceControllerPlugin(OgdchBaseControllerPlugin):
    plugins.implements(plugins.IResourceController, inherit=True)

    # IResourceController
    def before_show(self, res_dict):
        u'''
        Extensions will receive the validated data dict before the resource
        is ready for display.

        Be aware that this method is not only called for UI display, but also
        in other methods like when a resource is deleted because showing a
        package is used to get access to the resources in a package.
        '''
        res_dict = pu.ogdch_reduce_simple_ckandict_to_one_language(res_dict)
        res_dict['name'] = res_dict.get('title')
        res_dict['format'] = pu.ogdch_set_resource_format(res_dict, self.format_mapping)
        log.debug("IResourceController before_view: res_dict {}".format(res_dict))
        return res_dict
