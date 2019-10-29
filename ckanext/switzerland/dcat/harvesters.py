import json
import os
import hashlib
import traceback

import ckan.plugins as p
import ckan.logic as logic
import ckan.model as model

from ckanext.dcat.harvesters.rdf import DCATRDFHarvester
from ckanext.dcat.processors import RDFParserException
from ckanext.dcat.interfaces import IDCATRDFHarvester
from ckanext.harvest.model import HarvestObject

from processors import SwissDCATRDFParser
import helpers as tk_dcat

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

        if 'shacl_validation_file' in source_config_obj:
            shapedir = tk_dcat.get_shacl_shapedir_from_config()
            shapefilepath = os.path.join(
                shapedir, source_config_obj['shacl_validation_file'])
            if not os.path.exists(shapefilepath):
                raise ValueError('Shacl shape file does not exist in path {}'
                                 .format(shapedir))

        return source_config

    def _set_gather_config(self, raw_config):
        """sets config for the gather stage"""
        if raw_config:
            config = json.loads(raw_config)
        else:
            config = {}
        config['rdf_format'] = config.get("rdf_format", None)
        config['shacl_validation_file'] = config.get(
            "shacl_validation_file", None)
        config['shacl_validation'] = bool(config['shacl_validation_file'])
        log.debug('SHACL configuration: {}'.format(config))
        return config

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
        resource_mapping = {r.get('identifier'): r.get('id') for r in existing_resources if r.get('identifier')}  # noqa

        # Try to match existing identifiers with new ones
        # Note: in ckanext-dcat a mapping is already done based on the URI
        #       which will be overwritten here, i.e. the mapping by identifier
        #       has precedence
        for resource in dataset_dict.get('resources'):
            identifier = resource.get('identifier')
            if identifier and identifier in resource_mapping:
                resource['id'] = resource_mapping[identifier]

    def gather_stage(self, harvest_job): # noqa

        log.debug('In swiss dcat harvester gather_stage')

        gather_config = self._set_gather_config(harvest_job.source.config)

        # Get file contents of first page
        next_page_url = harvest_job.source.url

        guids_in_source = []
        object_ids = []
        last_content_hash = None
        page_count = 0

        while next_page_url:
            next_page_url, before_download_errors = \
                self.before_download(next_page_url, harvest_job)
            page_count += 1

            for error_msg in before_download_errors:
                self._save_gather_error(error_msg, harvest_job)

            if not next_page_url:
                return []

            content, rdf_format = self._get_content_and_type(
                next_page_url, harvest_job, 1,
                content_type=gather_config['rdf_format'])

            content_hash = hashlib.md5()
            if content:
                content_hash.update(content)

            if last_content_hash:
                if content_hash.digest() == last_content_hash.digest():
                    log.warning("Remote content was the same even when using a paginated URL, skipping") # noqa
                    break
            else:
                last_content_hash = content_hash

            content, after_download_errors = \
                self.after_download(content, harvest_job)

            for error_msg in after_download_errors:
                self._save_gather_error(error_msg, harvest_job)

            if not content:
                return []

            parser = SwissDCATRDFParser()

            try:
                # the harvest source is parsed
                # when the shacl validation failed the result
                # will be False
                log.debug("SHACL parsing page {} shacl validation: {}"
                          .format(page_count,
                                  gather_config['shacl_validation']))
                parser.parse(
                    content,
                    _format=rdf_format,
                    harvest_job=harvest_job,
                    page_count=page_count,
                    shacl_validation=gather_config['shacl_validation'],
                    shacl_file=gather_config['shacl_validation_file'],
                )
                if gather_config['shacl_validation']:
                    # in case of shacl validation errors they are
                    # reported as gather errors per page that was parsed
                    msg_count = 0
                    shacl_error_dict = parser.shaclresults_grouped()
                    if shacl_error_dict:
                        log.debug('SHACL error node count: {}'
                                  .format(len(shacl_error_dict.keys())))
                        for node in shacl_error_dict.keys():
                            for message in shacl_error_dict[node]:
                                msg_count += 1
                                self._save_gather_error(
                                    message, harvest_job)
                        log.debug('SHACL error message count: {}'
                                  .format(msg_count))
                        self._save_gather_error(
                            "there were {} shacl shape errors in total"
                            .format(msg_count),
                            harvest_job)

            except RDFParserException, e:
                self._save_gather_error('Error parsing the RDF file: {0}'
                                        .format(e), harvest_job)
                return []

            try:

                source_dataset = model.Package.get(harvest_job.source.id)

                for dataset in parser.datasets():
                    if not dataset.get('name'):
                        dataset['name'] = self._gen_new_name(dataset['title'])

                    # Unless already set by the parser,
                    # get the owner organization (if any)
                    # from the harvest source dataset
                    if not dataset.get('owner_org'):
                        if source_dataset.owner_org:
                            dataset['owner_org'] = source_dataset.owner_org

                    # Try to get a unique identifier for the harvested dataset
                    guid = self._get_guid(dataset,
                                          source_url=source_dataset.url)

                    if not guid:
                        self._save_gather_error(
                            'Could not get a unique identifier for dataset: {0}' # noqa
                                .format(dataset), harvest_job)
                        continue

                    dataset['extras'].append({'key': 'guid', 'value': guid})
                    guids_in_source.append(guid)

                    obj = HarvestObject(guid=guid, job=harvest_job,
                                        content=json.dumps(dataset))

                    obj.save()
                    object_ids.append(obj.id)
            except Exception, e:
                self._save_gather_error(
                    'Error when processsing dataset: %r / %s'
                    % (e, traceback.format_exc()), harvest_job)
                return []

            # get the next page
            next_page_url = parser.next_page()

        # Check if some datasets need to be deleted
        object_ids_to_delete = self._mark_datasets_for_deletion(
            guids_in_source, harvest_job)

        object_ids.extend(object_ids_to_delete)

        return object_ids
