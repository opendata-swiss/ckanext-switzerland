import pysolr
import itertools
import json
import re
import csv
import subprocess
import rdflib
from unidecode import unidecode
from collections import OrderedDict
from ckan.plugins.toolkit import get_or_bust, side_effect_free
from ckan.logic import ActionError, NotFound, ValidationError
from ckan.exceptions import CkanConfigurationException
import ckan.plugins.toolkit as tk
from ckan.lib.search.common import make_connection
from ckanext.harvest.model import HarvestSource, HarvestJob, HarvestObject
from ckanext.dcat.processors import RDFParserException
from ckanext.switzerland.dcat.shaclprocessor import (
    ShaclParser, SHACLParserException)
import helpers as ogdch_helpers

import logging
log = logging.getLogger(__name__)

FORMAT_TURTLE = 'ttl'
DATA_IDENTIFIER = 'data'
RESULT_IDENTIFIER = 'result'


@side_effect_free
def ogdch_counts(context, data_dict):
    '''
    Return the following data about our ckan instance:
    - total number of datasets
    - number of datasets per group
    - total number of showcases
    - total number of organisations (including all levels of the hierarchy)
    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}

    # group_list contains the number of datasets in the 'packages' field
    groups = tk.get_action('group_list')(req_context, {'all_fields': True})
    group_count = OrderedDict()
    for group in groups:
        group_count[group['name']] = group['package_count']

    return {
        'total_dataset_count': ogdch_helpers.get_dataset_count('dataset'), # noqa
        'showcase_count': ogdch_helpers.get_dataset_count('showcase'), # noqa
        'groups': group_count,
        'organization_count': ogdch_helpers.get_org_count(),
    }


@side_effect_free  # noqa
def ogdch_package_show(context, data_dict):  # noqa
    """
    custom package_show logic that returns a dataset together
    with related datasets, showcases and terms of use
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name'], 'for_view': True})
    id = get_or_bust(data_dict, 'id')

    result = tk.get_action('package_show')(context, {'id': id})
    if result:
        if result.get('see_alsos'):
            for item in result.get('see_alsos'):
                try:
                    related_dataset = tk.get_action('ogdch_dataset_by_identifier')(  # noqa
                        context, {'identifier': item.get('dataset_identifier')})  # noqa
                    if related_dataset:
                        item['title'] = related_dataset['title']
                        item['name'] = related_dataset['name']
                except:
                    continue

        try:
            showcases = ogdch_helpers.get_showcases_for_dataset(id=id)
            result['showcases'] = showcases
        except:
            pass

        try:
            result['terms_of_use'] = tk.get_action('ogdch_dataset_terms_of_use')(  # noqa
                context, {'id': id})
        except:
            raise "Terms of Use could not be found for dataset {}".format(id)

        return result
    else:
        raise NotFound


@side_effect_free
def ogdch_content_headers(context, data_dict):
    '''
    Returns some headers of a remote resource
    '''
    url = get_or_bust(data_dict, 'url')
    response = ogdch_helpers.get_content_headers(url)
    return {
        'status_code': response.status_code,
        'content-length': response.headers.get('content-length', ''),
        'content-type': response.headers.get('content-type', ''),
    }


@side_effect_free
def ogdch_dataset_terms_of_use(context, data_dict):
    '''
    Returns the terms of use for the requested dataset.

    By definition the terms of use of a dataset corresponds
    to the least open rights statement of all distributions of
    the dataset
    '''
    terms = [
        'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
        'NonCommercialAllowed-CommercialAllowed-ReferenceRequired',
        'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired',
        'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired',
        'ClosedData',
    ]
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    req_context = {'user': user['name']}
    pkg_id = get_or_bust(data_dict, 'id')
    pkg = tk.get_action('package_show')(req_context, {'id': pkg_id})

    least_open = None
    for res in pkg['resources']:
        if 'rights' in res:
            if res['rights'] not in terms:
                least_open = 'ClosedData'
                break
            if least_open is None:
                least_open = res['rights']
                continue
            if terms.index(res['rights']) > terms.index(least_open):
                least_open = res['rights']

    if least_open is None:
        least_open = 'ClosedData'

    return {
        'dataset_rights': least_open
    }


@side_effect_free
def ogdch_dataset_by_identifier(context, data_dict):
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name']})
    identifier = get_or_bust(data_dict, 'identifier')

    param = 'identifier:%s' % identifier
    result = tk.get_action('package_search')(context, {'fq': param})
    try:
        return result['results'][0]
    except (KeyError, IndexError, TypeError):
        raise NotFound


@side_effect_free
def ogdch_autosuggest(context, data_dict):
    q = get_or_bust(data_dict, 'q')
    lang = get_or_bust(data_dict, 'lang')
    fq = data_dict.get('fq', '')

    if fq:
        fq = 'NOT private AND %s' % fq
    else:
        fq = 'NOT private'

    # parse language from values like de_CH
    if len(lang) > 2:
        lang = lang[:2]

    if lang not in ['en', 'it', 'de', 'fr']:
        raise ValidationError('lang must be one of [en, it, de, fr]')

    handler = '/suggest_%s' % lang
    suggester = 'ckanSuggester_%s' % lang

    solr = make_connection()
    try:
        log.debug(
            'Loading suggestions for %s (lang: %s, fq: %s)' % (q, lang, fq)
        )
        results = solr.search(
            '',
            search_handler=handler,
            **{'suggest.q': q, 'suggest.count': 10, 'suggest.cfq': fq}
        )
        suggestions = results.raw_response['suggest'][suggester].values()[0]  # noqa

        def highlight(term, q):
            if '<b>' in term:
                return term
            clean_q = unidecode(q)
            clean_term = unidecode(term)

            re_q = re.escape(clean_q)
            m = re.search(re_q, clean_term, re.I)
            if m:
                replace_text = term[m.start():m.end()]
                term = term.replace(replace_text, '<b>%s</b>' % replace_text)
            return term

        terms = [highlight(suggestion['term'], q) for suggestion in suggestions['suggestions']]  # noqa
        return list(set(terms))
    except pysolr.SolrError as e:
        log.exception('Could not load suggestions from solr: %s' % e)
    raise ActionError('Error retrieving suggestions from solr')


def ogdch_cleanup_harvestjobs(context, data_dict):
    """
    cleans up the database for harvest objects and related tables for all
    harvesting jobs except the latest
    'ckanext.switzerland.number_harvest_jobs_per_source' is the corresponding
    configuration parameter on how many jobs to keep per source
    The command can be called with or without a source. In the later case all
    sources are cleaned.
    """

    # check access rights
    tk.check_access('harvest_sources_clear', context, data_dict)
    model = context['model']

    # get sources from data_dict
    if 'harvest_source_id' in data_dict:
        harvest_source_id = data_dict['harvest_source_id']
        source = HarvestSource.get(harvest_source_id)
        if not source:
            log.error('Harvest source {} does not exist'.format(
                harvest_source_id))
            raise NotFound('Harvest source {} does not exist'.format(
                harvest_source_id))
        sources_to_cleanup = [source]
    else:
        sources_to_cleanup = model.Session.query(HarvestSource).all()

    # get number of jobs to keep form data_dict
    if 'number_of_jobs_to_keep' in data_dict:
        number_of_jobs_to_keep = data_dict['number_of_jobs_to_keep']
    else:
        log.error(
            'Configuration missing for number of harvest jobs to keep')
        raise ValidationError(
            'Configuration missing for number of harvest jobs to keep')

    dryrun = data_dict.get("dryrun", False)

    log.info('Harvest job cleanup called for sources: {},'
             'configuration: {}'.format(
                 ', '.join([s.id for s in sources_to_cleanup]),
                 data_dict))

    # store cleanup result
    cleanup_result = {}
    for source in sources_to_cleanup:

        # get jobs ordered by their creations date
        delete_jobs = model.Session.query(HarvestJob) \
            .filter(HarvestJob.source_id == source.id) \
            .filter(HarvestJob.status == 'Finished') \
            .order_by(HarvestJob.created.desc()).all()[number_of_jobs_to_keep:]

        # decide which jobs to keep or delete on their order
        delete_jobs_ids = [job.id for job in delete_jobs]

        if not delete_jobs:
            log.debug(
                'Cleanup harvest jobs for source {}: nothing to do'
                .format(source.id))
        else:
            # log all job for a source with the decision to delete or keep them
            log.debug('Cleanup harvest jobs for source {}: delete jobs: {}'
                      .format(source.id, delete_jobs_ids))

            # get harvest objects for harvest jobs
            delete_objects_ids = \
                model.Session.query(HarvestObject.id) \
                .filter(HarvestObject.harvest_job_id.in_(
                    delete_jobs_ids)).all()
            delete_objects_ids = list(itertools.chain(
                *delete_objects_ids))

            # log all objects to delete
            log.debug(
                'Cleanup harvest objects for source {}: delete {} objects'
                .format(source.id, len(delete_objects_ids)))

            # perform delete
            sql = '''begin;
            delete from harvest_object_error
            where harvest_object_id in ('{delete_objects_values}');
            delete from harvest_object_extra
            where harvest_object_id in ('{delete_objects_values}');
            delete from harvest_object
            where id in ('{delete_objects_values}');
            delete from harvest_gather_error
            where harvest_job_id in ('{delete_jobs_values}');
            delete from harvest_job
            where id in ('{delete_jobs_values}');
            commit;
            '''.format(delete_objects_values="','".join(delete_objects_ids),
                       delete_jobs_values="','".join(delete_jobs_ids))

            # only execute the sql if it is not a dry run
            if not dryrun:
                model.Session.execute(sql)

                # reindex after deletions
                tk.get_action('harvest_source_reindex')(
                    context, {'id': source.id})

            # fill result
            cleanup_result[source.id] = {
                'deleted_jobs': delete_jobs,
                'deleted_nr_objects': len(delete_objects_ids)}

            log.error(
                'cleaned resource and shacl result directories {}'
                .format(source.id))

    # return result of action
    return {'sources': sources_to_cleanup,
            'cleanup': cleanup_result}


def ogdch_shacl_validate(context, data_dict):  # noqa
    """
    validates a harvest source against a shacl shape
    """

    # get sources from data_dict
    if 'harvest_source_id' in data_dict:
        harvest_source_id = data_dict['harvest_source_id']
        harvest_source = HarvestSource.get(harvest_source_id)
        if not harvest_source:
            raise NotFound('Harvest source {} does not exist'.format(
                harvest_source_id))
    else:
        raise NotFound('Configuration missing for harvest source')

    datapath = data_dict['datapath']
    resultpath = data_dict['resultpath']
    shapefilepath = data_dict['shapefilepath']
    csvpath = data_dict['csvpath']
    shaclcommand = data_dict['shaclcommand']

    log.info('shacl_validate called for source: {},'
             'configuration: {}'
             .format(harvest_source_id, data_dict))

    # get rdf parse config for harvest source
    rdf_format = json.loads(harvest_source.config)\
        .get("rdf_format", "xml")

    # parse harvest_source
    data_rdfgraph = rdflib.Graph()

    # parse data from harvest source url
    try:
        data_rdfgraph.parse(harvest_source.url, format=rdf_format)
    except RDFParserException, e:
        raise RDFParserException(
            'Error parsing the RDF file during shacl validation: {0}'
            .format(e))

    log.debug("parsed source url {} with format {}"
              .format(harvest_source.url, rdf_format))

    # write parsed data to file
    try:
        with open(datapath, 'w') as datawriter:
            datawriter.write(data_rdfgraph.serialize(format='turtle'))
    except CkanConfigurationException as e:
        raise CkanConfigurationException(
            'Configuration during shacl validation: {0}'
            .format(e))

    log.debug("datagraph was serialized to turtle: {}"
              .format(datapath))

    # execute the shacl command
    try:
        with open(resultpath, 'w') as resultwriter:
            subprocess.call(
                [shaclcommand,
                 "validate",
                 "--shapes", shapefilepath,
                 "--data", datapath],
                stdout=resultwriter)
    except CkanConfigurationException as e:
        raise CkanConfigurationException(
            'Configuration during shacl validation: {0}'
            .format(e))

    log.debug("shacl command was executed: {}"
              .format(resultpath))

    shaclparser = ShaclParser(resultpath, harvest_source_id)
    try:
        shaclparser.parse()
    except SHACLParserException as e:
        raise CkanConfigurationException(
            'Exception parsing result: {0}. Please try again.'
            .format(e))

    log.debug("shacl parser is initialized: {}"
              .format(resultpath, harvest_source_id))

    # write shacl errors to csv file
    with open(csvpath, 'w') as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=shaclparser.resultdictkeys,
            delimiter='|', restval='')
        writer.writeheader()
        for resultdict in shaclparser.shaclresults():
            try:
                writer.writerow(resultdict)
            except UnicodeEncodeError as e:
                resultdict = {
                    shaclparser.resultdictkey_harvestsourceid:
                        harvest_source_id,
                    shaclparser.resultdictkey_parseerror: e
                }
                writer.writerow(resultdict)
