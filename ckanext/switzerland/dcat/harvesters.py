from ckanext.dcat.harvesters.rdf import DCATRDFHarvester

import logging
log = logging.getLogger(__name__)


class SwissDCATRDFHarvester(DCATRDFHarvester):
    def info(self):
        return {
            'name': 'dcat_ch_rdf',
            'title': 'DCAT-AP Switzerland RDF Harvester',
            'description': 'Harvester for DCAT-AP Switzerland datasets from an RDF graph'  # noqa
        }

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

        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'uri' and extra['value']:
                return extra['value']

        if dataset_dict.get('uri'):
            return dataset_dict['uri']

        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'identifier' and extra['value']:
                return extra['value']

        if dataset_dict.get('identifier'):
            guid = dataset_dict['identifier']
            # check if the owner_org matches the identifier
            if '@' in guid:
                org = guid.split('@')[-1]  # get last element
                if org != dataset_dict['owner_org']:
                    log.error(
                        'The organization in the dataset indentifier (%s) '
                        'does not match the organization in the harvester '
                        'config (%s)' % (org, dataset_dict['owner_org'])
                    )
                    return None
            return dataset_dict['identifier']

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
