import json

import ckan.plugins as p
import ckan.model as model

from ckanext.harvest.model import HarvestObject

from ckanext.dcat.parsers import RDFParserException, RDFParser
from ckanext.dcat.interfaces import IDCATRDFHarvester
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

    def gather_stage(self, harvest_job):  # noqa

        log.debug('In DCATRDFHarvester gather_stage')

        # Get file contents
        url = harvest_job.source.url

        for harvester in p.PluginImplementations(IDCATRDFHarvester):
            url, before_download_errors = harvester.before_download(
                url,
                harvest_job)

            for error_msg in before_download_errors:
                self._save_gather_error(error_msg, harvest_job)

            if not url:
                return False

        content = self._get_content(url, harvest_job, 1)

        # TODO: store content?
        for harvester in p.PluginImplementations(IDCATRDFHarvester):
            content, after_download_errors = harvester.after_download(
                content,
                harvest_job)

            for error_msg in after_download_errors:
                self._save_gather_error(error_msg, harvest_job)

        if not content:
            return False

        # TODO: profiles conf
        parser = RDFParser()
        # TODO: format conf
        try:
            parser.parse(content)
        except RDFParserException, e:
            self._save_gather_error(
                'Error parsing the RDF file: {0}'.format(e), harvest_job)
            return False

        guids_in_source = []
        object_ids = []
        for dataset in parser.datasets():
            if not dataset.get('name'):
                dataset['name'] = self._gen_new_name(dataset['title']['de'])

            # Unless already set by the parser, get the owner organization
            # (if any) from the harvest source dataset
            if not dataset.get('owner_org'):
                source_dataset = model.Package.get(harvest_job.source.id)
                if source_dataset.owner_org:
                    dataset['owner_org'] = source_dataset.owner_org

            # Try to get a unique identifier for the harvested dataset
            guid = self._get_guid(dataset)
            if not guid:
                log.error(
                    'Could not get a unique identifier for dataset: {0}'
                    .format(dataset))
                continue

            dataset['extras'].append({'key': 'guid', 'value': guid})
            guids_in_source.append(guid)

            obj = HarvestObject(guid=guid, job=harvest_job,
                                content=json.dumps(dataset))

            obj.save()
            object_ids.append(obj.id)

        # Check if some datasets need to be deleted
        object_ids_to_delete = self._mark_datasets_for_deletion(
            guids_in_source,
            harvest_job)

        object_ids.extend(object_ids_to_delete)

        return object_ids
