import ckan.plugins as p
import ckan.logic as logic

import json
from ckanext.dcat.harvesters.rdf import DCATRDFHarvester
from ckanext.dcat.interfaces import IDCATRDFHarvester
import ckan.model as model

import logging
log = logging.getLogger(__name__)


class SwissDCATRDFHarvester(DCATRDFHarvester):
    p.implements(IDCATRDFHarvester, inherit=True)

    harvest_job = None

    def info(self):
        return {
            'name': 'dcat_ch_rdf',
            'title': 'DCAT-AP Switzerland RDF Harvester',
            'description': 'Harvester for DCAT-AP Switzerland datasets from an RDF graph'  # noqa
        }

    def validate_config(self, source_config):
        source_config = super(SwissDCATRDFHarvester, self).validate_config(source_config)  # noqa

        if not source_config:
            return source_config

        source_config_obj = json.loads(source_config)

        if 'excluded_dataset_identifiers' in source_config_obj:
            excluded_dataset_identifiers = source_config_obj['excluded_dataset_identifiers']  # noqa
            if not isinstance(excluded_dataset_identifiers, list):
                raise ValueError('excluded_dataset_identifiers must be '
                                 'a list of strings')
                if not all(isinstance(item, basestring)
                           for item in excluded_dataset_identifiers):
                    raise ValueError('excluded_dataset_identifiers must be '
                                     'a list of strings')

        return source_config

    def before_download(self, url, harvest_job):
        # save the harvest_job on the instance
        self.harvest_job = harvest_job

        # fix broken URL for City of Zurich
        url = url.replace('ogd.global.szh.loc', 'data.stadt-zuerich.ch')
        return url, []

    def _get_guid(self, dataset_dict, source_url=None):  # noqa
        '''
        Try to get a unique identifier for a harvested dataset
        It will be the first found of:
         * URI (rdf:about)
         * dcat:identifier
         * Source URL + Dataset name
         * Dataset name
         The last two are obviously not optimal, as depend on title, which
         might change.
         Returns None if no guid could be decided.
        '''
        guid = None

        if dataset_dict.get('identifier'):
            guid = dataset_dict['identifier']
            # check if the owner_org matches the identifier
            try:
                if '@' in guid:
                    org_name = guid.split('@')[-1]  # get last element
                    org = model.Group.by_name(org_name)
                    if not org:
                        error_msg = (
                            'The organization in the dataset identifier (%s) '
                            'does not not exist. ' % org_name
                        )
                        log.error(error_msg)
                        self._save_gather_error(error_msg, self.harvest_job)
                        return None

                    if org.id != dataset_dict['owner_org']:
                        error_msg = (
                            'The organization in the dataset identifier (%s) '
                            'does not match the organization in the harvester '
                            'config (%s)' % (org.id, dataset_dict['owner_org'])
                        )
                        log.error(error_msg)
                        self._save_gather_error(error_msg, self.harvest_job)
                        return None
            except:
                log.exception("An error occured")
                return None
            return dataset_dict['identifier']

        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'uri' and extra['value']:
                return extra['value']

        if dataset_dict.get('uri'):
            return dataset_dict['uri']

        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'identifier' and extra['value']:
                return extra['value']

        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'dcat_identifier' and extra['value']:
                return extra['value']

        if dataset_dict.get('name'):
            guid = dataset_dict['name']
            if source_url:
                guid = source_url.rstrip('/') + '/' + guid

        return guid

    def _gen_new_name(self, title):
        try:
            return super(SwissDCATRDFHarvester, self)._gen_new_name(title['de'])  # noqa
        except TypeError:
            return super(SwissDCATRDFHarvester, self)._gen_new_name(title)  # noqa

    def before_create(self, harvest_object, dataset_dict, temp_dict):
        try:
            source_config_obj = json.loads(harvest_object.job.source.config)

            for excluded_dataset_identifier in source_config_obj.get('excluded_dataset_identifiers', []):  # noqa
                if excluded_dataset_identifier == dataset_dict.get('identifier'):  # noqa
                    dataset_dict.clear()
        except ValueError:
            # nothing configured
            pass

    def before_update(self, harvest_object, dataset_dict, temp_dict):
        # get existing pkg_dict with incoming pkg_name
        site_user = logic.get_action('get_site_user')(
            {'model': model, 'ignore_auth': True}, {})
        context = {
            'model': model,
            'session': model.Session,
            'ignore_auth': True,
            'user': site_user['name'],
        }
        existing_pkg = p.toolkit.get_action('package_show')(context, {
            'id': dataset_dict.get('name')})

        # get existing resource-identifiers
        existing_resources = existing_pkg.get('resources')
        existing_resource_ids = []
        for existing_resource in existing_resources:
            existing_resource_ids.append(existing_resource.get('identifier'))

        # check if incoming resource-identifier already match with existing resource-identifier
        for resource in dataset_dict.get('resources'):
            if resource.get('identifier') in existing_resource_ids:
                # retrieve ckan-id and set it in dataset_dict
                for existing_resource in existing_resources:
                    if existing_resource.get('identifier') == resource.get('identifier'):
                        resource['id'] = existing_resource['id']

        pass
