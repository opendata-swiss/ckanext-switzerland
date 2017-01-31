import ckan.plugins as p

from ckan.lib.helpers import json
from ckanext.dcat.harvesters.rdf import DCATRDFHarvester
from ckanext.dcat.interfaces import IDCATRDFHarvester
import ckan.model as model

import logging
log = logging.getLogger(__name__)


class SwissDCATRDFHarvester(DCATRDFHarvester):
    p.implements(IDCATRDFHarvester, inherit=True)

    def info(self):
        return {
            'name': 'dcat_ch_rdf',
            'title': 'DCAT-AP Switzerland RDF Harvester',
            'description': 'Harvester for DCAT-AP Switzerland datasets from an RDF graph'  # noqa
        }

    def _set_config(self, config_str):
        if config_str:
            self.config = json.loads(config_str)
        else:
            self.config = {}
        log.debug('Using config: %r' % self.config)

    def before_download(self, url, harvest_job):
        # fix broken URL for City of Zurich
        url = url.replace('ogd.global.szh.loc', 'data.stadt-zuerich.ch')
        try:
            self._set_config(harvest_job.source.config)
        except:
            pass
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
                        log.error(
                            'The organization in the dataset identifier (%s) '
                            'does not not exist. ' % org_name
                        )
                        return None

                    if org.id != dataset_dict['owner_org']:
                        log.error(
                            'The organization in the dataset identifier (%s) '
                            'does not match the organization in the harvester '
                            'config (%s)' % (org.id, dataset_dict['owner_org'])
                        )
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
        if self.config.get('excluded-dataset-identifiers'):
            for excluded_dataset_identifier in self.config.get('excluded-dataset-identifiers'):  # noqa
                if excluded_dataset_identifier == dataset_dict.get('identifier'):  # noqa
                    dataset_dict = None
