# encoding: utf-8

import logging
import os
from urllib import urlencode
from six import string_types
import ckan.model as model
from ckan.logic import get_action
from ckan.lib.plugins import lookup_group_controller
from ckan.common import c, config, _, request, OrderedDict
import ckan.lib.helpers as h
import ckan.authz as authz
import ckan.lib.search as search
import ckan.controllers.group as group
import ckanext.switzerland.backend_helpers as bh

log = logging.getLogger(__name__)


class OgdchGroupController(group.GroupController):

    def _index_template(self, group_type):
        return bh.ogdch_template_choice(
            template_frontend=os.path.join('group', 'index_ogdch.html'),
            template_backend=os.path.join('group', 'index.html')
        )

    def _read_template(self, group_type):
        return bh.ogdch_template_choice(
            template_frontend=os.path.join('group', 'read_ogdch.html'),
            template_backend=os.path.join('group', 'read.html')
        )

    def _read(self, id, limit, group_type):  # noqa
        """
        This controller replaces the GroupController controller
        from CKAN. It uses the filter query (fq) parameter to query
        facets in Solr instead of the query parameter (q). If the
        query parameter is used the search always returns "no results found"
        when combining a search term with facets.
        Unfortunately there are no clean extension points in the
        GroupController, so that the _read() method
        had to be overridden completely.

        This is common code used by both read and bulk_process
        """
        log.error("OGDCHSPY in ogdch group search controller")
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}

        q = c.q = request.params.get('q', '')
        # Search within group
        if c.group_dict.get('is_organization'):
            fq = 'owner_org:"%s"' % c.group_dict.get('id')
        else:
            fq = 'groups:"%s"' % c.group_dict.get('name')

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
            params = [(k, v.encode('utf-8') if isinstance(v, string_types)
                       else str(v)) for k, v in params]
            return url + u'?' + urlencode(params)

        def drill_down_url(**by):
            return h.add_url_param(alternative_url=None,
                                   controller='group', action='read',
                                   extras=dict(id=c.group_dict.get('name')),
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            controller = lookup_group_controller(group_type)
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller=controller, action='read',
                                      extras=dict(id=c.group_dict.get('name')))

        c.remove_field = remove_field

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        try:
            c.fields = []
            c.fields_grouped = {}
            search_extras = {}
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq += ' %s: "%s"' % (param, value)
                        if param not in c.fields_grouped:
                            c.fields_grouped[param] = [value]
                        else:
                            c.fields_grouped[param].append(value)
                    else:
                        search_extras[param] = value

            facets = OrderedDict()

            default_facet_titles = {'organization': _('Organizations'),
                                    'groups': _('Groups'),
                                    'tags': _('Tags'),
                                    'res_format': _('Formats'),
                                    'license_id': _('Licenses')}

            for facet in h.facets():
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            self._update_facet_titles(facets, group_type)

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq,
                'include_private': True,
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

            c.search_facets = query['search_facets']
            c.search_facets_limits = {}
            for facet in c.search_facets.keys():
                limit = int(request.params.get('_%s_limit' % facet,
                                               config.get(
                                                   'search.facets.default',
                                                   10)))
                c.search_facets_limits[facet] = limit
            c.page.items = query['results']

            c.sort_by_selected = sort_by

        except search.SearchError as se:
            log.error('Group search error: %r', se.args)
            c.query_error = True
            c.search_facets = {}
            c.page = h.Page(collection=[])

        self._setup_template_variables(
            context,
            {'id': id},
            group_type=group_type
        )

