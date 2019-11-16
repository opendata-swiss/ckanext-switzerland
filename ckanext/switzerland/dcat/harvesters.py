import json
import os
import subprocess

import ckan.plugins as p
import ckan.logic as logic
import ckan.model as model
from ckan.exceptions import CkanConfigurationException

from ckanext.dcat.harvesters.rdf import DCATRDFHarvester
from ckanext.dcat.processors import RDFParser, RDFParserException
from ckanext.dcat.utils import url_to_rdflib_format
from ckanext.dcat.interfaces import IDCATRDFHarvester

from shaclprocessor import ShaclParser, SHACLParserException
import helpers as tk_dcat

import logging
log = logging.getLogger(__name__)

SHACLREPORTLEVEL_SUMMARY = 'summary'
SHACLREPORTLEVEL_DETAIL = 'detail'
FORMAT_TURTLE = 'ttl'
DATA_IDENTIFIER = 'data'
RESULT_IDENTIFIER = 'result'


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
            shapedir = tk_dcat.get_shacl_shapedir()
            shapefilepath = os.path.join(
                shapedir, source_config_obj['shacl_validation_file'])
            if not os.path.exists(shapefilepath):
                raise ValueError('Shacl shape file does not exist in path {}'
                                 .format(shapefilepath))

        if 'shacl_report_level' in source_config_obj:
            shacl_report_level = source_config_obj['shacl_report_level']
            if shacl_report_level not in [SHACLREPORTLEVEL_SUMMARY,
                                          SHACLREPORTLEVEL_DETAIL]:
                raise ValueError('"shacl_report_level" must be {} or {}'
                                 .format(SHACLREPORTLEVEL_SUMMARY,
                                         SHACLREPORTLEVEL_DETAIL))
        return source_config

    def _prepare_shacl_validation(self, harvest_job):
        """sets config for the gather stage"""
        if harvest_job.source.config:
            config = json.loads(harvest_job.source.config)
            self.rdf_format = url_to_rdflib_format(config.get("rdf_format"))
            self.shacl_validation_file = \
                config.get("shacl_validation_file", None)
            self.shacl_report_level = config.get("shacl_report_level", None)
        self.resultdir = tk_dcat.make_shacl_result_job_dir(
            harvest_job.source_id, harvest_job.id)
        tk_dcat.make_shacl_result_job_dir(
            harvest_job.source_id, harvest_job.id)
        log.debug("shacl resultdir prepared {}".format(self.resultdir))

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

    def after_download(self, content, harvest_job):

        if not hasattr(self, 'resultdir'):
            # save config for shacl validation
            self._prepare_shacl_validation(harvest_job)

        log.debug("""SHACL resultdir should exist now {}"""
                  .format(self.resultdir))

        after_download_errors = []

        # perform shacl validation
        contentparser = RDFParser()
        try:
            contentparser.parse(content, _format=self.rdf_format)

            # TODO use pyshacl instead of file-io when
            #      ckan is on python version 3
            shacl_command = tk_dcat.get_shacl_command_from_config()

            datapath = tk_dcat.get_shacl_file_path(
                self.resultdir,
                DATA_IDENTIFIER,
                FORMAT_TURTLE)

            resultpath = tk_dcat.get_shacl_file_path(
                self.resultdir,
                RESULT_IDENTIFIER,
                FORMAT_TURTLE)

            shapefilepath = tk_dcat.get_shacl_shape_file_path(
                self.shacl_validation_file)

            log.debug("""SHACL performing shacl evaluation:
                      evaluating {} against {}"""
                      .format(datapath, self.shacl_validation_file))

            with open(datapath, 'w') as datawriter:
                datawriter.write(contentparser.g.serialize(format='turtle'))
            log.debug("SHACL data serialized as turtle: {}"
                      .format(datapath))

            with open(resultpath, 'w') as resultwriter:
                subprocess.call(
                    [shacl_command,
                     "validate",
                     "--shapes", shapefilepath,
                     "--data", datapath],
                    stdout=resultwriter)

            shaclparser = ShaclParser(
                resultpath, harvest_job.source_id)
            shaclparser.parse()

            if self.shacl_report_level == SHACLREPORTLEVEL_DETAIL:
                after_download_errors.extend(
                    shaclparser.shacl_error_messages())
            else:
                after_download_errors.append(
                    "there were {} shacl errors on the page"
                    .format(len(shaclparser.shacl_error_messages())))

            shaclparser.write_csv_file()

        except SHACLParserException as e:
            after_download_errors.append(
                'Error parsing shacl results: {0}'
                .format(e))

        except CkanConfigurationException as e:
            after_download_errors.append(
                'Configuration during shacl validation: {0}'
                .format(e))
        except RDFParserException, e:
            after_download_errors.append(
                'Error parsing the RDF file during shacl validation: {0}'
                .format(e))

        return content, after_download_errors
