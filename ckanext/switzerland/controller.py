from urllib import urlencode
import logging

from ckan.plugins import toolkit as tk
import ckan.model as model
import ckan.logic as logic
import ckan.lib.maintain as maintain
import ckan.lib.plugins
from ckan.common import c, _, g, request, response, OrderedDict
import ckan.lib.helpers as h
import ckan.authz as authz
import ckan.lib.search as search
import ckan.lib.base as base
from ckan.controllers.api import ApiController
from ConfigParser import ConfigParser
from email.mime.text import MIMEText
from urlparse import urlparse

import pylons
import json
import smtplib
import requests

from ckanext.hierarchy.controller import _children_name_list
import ckan.controllers.organization as organization
import ckanext.hierarchy.helpers as hierarchy_helpers

import ckan.controllers.group as group

lookup_group_controller = ckan.lib.plugins.lookup_group_controller
log = logging.getLogger(__name__)
get_action = logic.get_action
NotFound = logic.NotFound
abort = tk.abort


class OgdchOrganizationSearchController(organization.OrganizationController):
    """
    This controller replaces the HierarchyOrganizationController controller
    from ckanext-hierarchy. It makes sure, that datasets of sub-organizations
    are included on the organisation detail page and uses the filter query (fq)
    parameter of Solr to limit the search instead of the owner_org query used
    in CKAN core.
    In order to replace HierarchyOrganizationController it's important to load
    the ogdch_org_search plugin _after_ the hierarchy_display plugin in the
    plugin list of the active ini file. Unfortunately there are no clean
    extension points in the OrganizationController, so that the _read() method
    had to be overridden completely.
    """
    def _read(self, id, limit, group_type):  # noqa
        c.include_children_selected = False

        if not c.group_dict.get('is_organization'):
            return

        ''' This is common code used by both read and bulk_process'''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}

        c.description_formatted = \
            h.render_markdown(c.group_dict.get('description'))

        context['return_query'] = True

        # c.group_admins is used by CKAN's legacy (Genshi) templates only,
        # if we drop support for those then we can delete this line.
        c.group_admins = authz.get_group_or_org_admin_ids(c.group.id)

        page = h.get_page_number(request.params)

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']
        sort_by = request.params.get('sort', None)

        def search_url(params):
            controller = lookup_group_controller(group_type)
            action = 'bulk_process' if c.action == 'bulk_process' else 'read'
            url = h.url_for(controller=controller, action=action, id=id)
            params = [(k, v.encode('utf-8') if isinstance(v, basestring)
                      else str(v)) for k, v in params]
            return url + u'?' + urlencode(params)

        def drill_down_url(**by):
            return h.add_url_param(alternative_url=None,
                                   controller='group', action='read',
                                   extras=dict(id=c.group_dict.get('name')),
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='group', action='read',
                                      extras=dict(id=c.group_dict.get('name')))

        c.remove_field = remove_field

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        try:
            q = c.q = request.params.get('q', '')
            fq = c.fq = request.params.get('fq', '')

            c.fields = []
            search_extras = {}
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq += ' %s: "%s"' % (param, value)
                    else:
                        search_extras[param] = value

            user_member_of_orgs = [org['id'] for org
                                   in h.organizations_available('read')]

            if (c.group and c.group.id in user_member_of_orgs):
                context['ignore_capacity_check'] = True
            else:
                fq += ' capacity:"public"'

            facets = OrderedDict()

            default_facet_titles = {
                'organization': _('Organizations'),
                'groups': _('Groups'),
                'tags': _('Tags'),
                'res_format': _('Formats'),
                'license_id': _('Licenses')
            }

            for facet in g.facets:
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            self._update_facet_titles(facets, group_type)

            if 'capacity' in facets and (group_type != 'organization' or
                                         not user_member_of_orgs):
                del facets['capacity']

            c.facet_titles = facets

            # filter by organization with fq (filter query)
            c.include_children_selected = True
            children = _children_name_list(
                hierarchy_helpers.group_tree_section(
                    c.group_dict.get('id'),
                    include_parents=False,
                    include_siblings=False
                ).get('children', [])
            )

            if not children:
                fq += ' organization:"%s"' % c.group_dict.get('name')
            else:
                fq += ' organization:("%s"' % c.group_dict.get('name')
                for name in children:
                    if name:
                        fq += ' OR "%s"' % name
                fq += ")"

            data_dict = {
                'q': q,
                'fq': fq,
                'facet.field': facets.keys(),
                'rows': limit,
                'sort': sort_by,
                'start': (page - 1) * limit,
                'extras': search_extras
            }

            context_ = dict((k, v) for (k, v) in context.items()
                            if k != 'schema')
            query = get_action('package_search')(context_, data_dict)

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )

            c.group_dict['package_count'] = query['count']
            c.facets = query['facets']
            maintain.deprecate_context_item('facets',
                                            'Use `c.search_facets` instead.')

            c.search_facets = query['search_facets']
            c.search_facets_limits = {}
            for facet in c.facets.keys():
                limit = int(request.params.get('_%s_limit' % facet,
                            g.facets_default_number))
                c.search_facets_limits[facet] = limit
            c.page.items = query['results']

            c.sort_by_selected = sort_by

        except search.SearchError, se:
            log.error('Group search error: %r', se.args)
            c.query_error = True
            c.facets = {}
            c.page = h.Page(collection=[])

        self._setup_template_variables(
            context,
            {'id': id},
            group_type=group_type
        )
        return


class OgdchGroupSearchController(group.GroupController):
    """
    This controller replaces the GroupController controller
    from CKAN. It uses the filter query (fq) parameter to query
    facets in Solr instead of the query parameter (q). If the
    query parameter is used the search always returns "no results found"
    when combining a search term with facets.
    Unfortunately there are no clean extension points in the
    GroupController, so that the _read() method
    had to be overridden completely.
    """

    def _read(self, id, limit, group_type):  # noqa
        ''' This is common code used by both read and bulk_process'''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}

        q = c.q = request.params.get('q', '')
        fq = ''
        # Search within group
        if c.group_dict.get('is_organization'):
            fq += ' owner_org:"%s"' % c.group_dict.get('id')
        else:
            fq += ' groups:"%s"' % c.group_dict.get('name')

        c.description_formatted = \
            h.render_markdown(c.group_dict.get('description'))

        context['return_query'] = True

        # c.group_admins is used by CKAN's legacy (Genshi) templates only,
        # if we drop support for those then we can delete this line.
        c.group_admins = authz.get_group_or_org_admin_ids(c.group.id)

        page = h.get_page_number(request.params)

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']
        sort_by = request.params.get('sort', None)

        def search_url(params):
            controller = lookup_group_controller(group_type)
            action = 'bulk_process' if c.action == 'bulk_process' else 'read'
            url = h.url_for(controller=controller, action=action, id=id)
            params = [(k, v.encode('utf-8') if isinstance(v, basestring)
                       else str(v)) for k, v in params]
            return url + u'?' + urlencode(params)

        def drill_down_url(**by):
            return h.add_url_param(alternative_url=None,
                                   controller='group', action='read',
                                   extras=dict(id=c.group_dict.get('name')),
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='group', action='read',
                                      extras=dict(id=c.group_dict.get('name')))

        c.remove_field = remove_field

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        try:
            c.fields = []
            search_extras = {}
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq += ' %s: "%s"' % (param, value)
                    else:
                        search_extras[param] = value

            user_member_of_orgs = [org['id'] for org
                                   in h.organizations_available('read')]

            if (c.group and c.group.id in user_member_of_orgs):
                context['ignore_capacity_check'] = True
            else:
                fq += ' capacity:"public"'

            facets = OrderedDict()

            default_facet_titles = {'organization': _('Organizations'),
                                    'groups': _('Groups'),
                                    'tags': _('Tags'),
                                    'res_format': _('Formats'),
                                    'license_id': _('Licenses')}

            for facet in g.facets:
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            self._update_facet_titles(facets, group_type)

            if 'capacity' in facets and (group_type != 'organization' or
                                         not user_member_of_orgs):
                del facets['capacity']

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq,
                'facet.field': facets.keys(),
                'rows': limit,
                'sort': sort_by,
                'start': (page - 1) * limit,
                'extras': search_extras
            }

            context_ = dict((k, v) for (k, v) in context.items()
                            if k != 'schema')
            query = get_action('package_search')(context_, data_dict)

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )

            c.group_dict['package_count'] = query['count']
            c.facets = query['facets']
            maintain.deprecate_context_item('facets',
                                            'Use `c.search_facets` instead.')

            c.search_facets = query['search_facets']
            c.search_facets_limits = {}
            for facet in c.facets.keys():
                limit = int(request.params.get('_%s_limit' % facet,
                                               g.facets_default_number))
                c.search_facets_limits[facet] = limit
            c.page.items = query['results']

            c.sort_by_selected = sort_by

        except search.SearchError, se:
            log.error('Group search error: %r', se.args)
            c.query_error = True
            c.facets = {}
            c.page = h.Page(collection=[])

        self._setup_template_variables(
            context,
            {'id': id},
            group_type=group_type
        )


class OgdchPermaController(base.BaseController):
    """
    This controller handles the permalinks
    """

    def read(self, id):
        """
        This action redirects requests to /perma/{identifier} to
        the corresponding /dataset/{slug} route
        """
        try:
            dataset = logic.get_action('ogdch_dataset_by_identifier')(
                {'for_view': True},
                {'identifier': id}
            )
            # redirect to dataset detail page
            tk.redirect_to(controller='package',
                           action='read',
                           id=dataset['name'])
        except NotFound:
            abort(404, _('Dataset not found'))


class DiscourseController(ApiController):

    # /api/ogdch_discourse_post_created/
    def post_created(self):
        '''Render the config template with the first custom title.'''

        discourse_post = json.loads(request.body)

        ckan_site_url = urlparse(pylons.config.get('ckan.site_url', None))
        ckan_hostname = ckan_site_url.hostname

        discourse_topic_url = urlparse(discourse_post[1]['referrer'])
        discourse_topic_url_endpoint = discourse_topic_url.geturl() + '.json'
        discourse_topic = requests.get(discourse_topic_url_endpoint, verify=False).json()

        for link in discourse_topic['details']['links']:
            log.error(link['url'])
            url = urlparse(link['url'])
            if link['domain'] == ckan_hostname and url.path.startswith('/dataset/'):
                dataset_url = link['url']
                package_id = dataset_url.split('/dataset/', 1)[1].replace('/', '')
                try:
                    package = tk.get_action('package_show')({'ignore_auth': True}, {'id': package_id})
                    self._notify_contactpoints(discourse_topic_url, dataset_url, package)
                except NotFound:
                    abort(404, _('The dataset {id} could not be found.').format(id=id))

    def _notify_contactpoints(self, discourse, package):

    def _notify_contactpoints(self, discourse_topic_url, dataset_url, package):

        smtp_host = pylons.config.get('smtp.server', None)
        smtp_port = pylons.config.get('smtp.host', None)
        from_mail = 'no-reply@ogdch.dev'

        for contact in package['contact_points']:
            receiver_mail = contact['email']
            receiver_name = contact['name']

            dataset_url = ckan_site_url + '/dataset/' + package['name']

            mail = 'Hello ' + receiver_name + '!\n\n'
            mail += 'A new post was created on Discourse at: ' + discourse_topic_url.geturl() + '\n'
            mail += 'You receive this mail as a contact point of the dataset '
            mail += 'of ' + package['name'] + ' at ' + dataset_url + ' \n'
            mail += 'To read the post follow this link: ' + discourse_topic_url.geturl()

            msg = MIMEText(mail)
            msg['Subject'] = 'Discourse Notification'
            msg['From'] = from_mail
            msg['To'] = receiver_mail

            log.error(msg)

            s = smtplib.SMTP(smtp_host, smtp_port)
            s.sendmail(from_mail, receiver_mail, msg.as_string())
            s.quit()

