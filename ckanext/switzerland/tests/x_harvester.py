# -*- coding: utf-8 -*-

import httpretty
import json
import nose
import os

import ckantoolkit.tests.helpers as h

import ckanext.harvest.model as harvest_model
from ckanext.harvest import queue

from ckanext.harvest.model import HarvestJob

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true
assert_raises = nose.tools.assert_raises

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)

mock_url = "http://mock-swiss-dcat.ch"

class FunctionalHarvestTest(object):
    @classmethod
    def setup_class(cls):
        h.reset_db()

        cls.gather_consumer = queue.get_gather_consumer()
        cls.fetch_consumer = queue.get_fetch_consumer()

    def setup(self):
        harvest_model.setup()

        queue.purge_queues()

        user_dict = h.call_action('user_create', name='testuser',
                                  email='testuser@example.com', password='password')
        org_context = {
            'user': user_dict['name'],
            'return_id_only': True
        }
        org_data_dict = {
            'name': 'geocat_org'
        }
        self.org_id = h.call_action('organization_create',
                                org_context, **org_data_dict)

    def teardown(self):
        h.reset_db()

    def _get_or_create_harvest_source(self, **kwargs):
        source_dict = {
            'title': 'Swiss Dcat harvester',
            'name': 'swiss-dcat-harvester',
            'url': mock_url,
            'source_type': 'swissdcat_harvester',
            'owner_org': self.org_id
        }

        source_dict.update(**kwargs)

        try:
            harvest_source = h.call_action('harvest_source_show',
                                           {}, **source_dict)
        except Exception as e:
            harvest_source = h.call_action('harvest_source_create',
                                           {}, **source_dict)

        return harvest_source

    def _create_harvest_job(self, harvest_source_id):
        harvest_job = h.call_action('harvest_job_create',
                                    {}, source_id=harvest_source_id)

        return harvest_job

    def _run_jobs(self, harvest_source_id=None):
        try:
            h.call_action('harvest_jobs_run',
                          {}, source_id=harvest_source_id)
        except Exception, e:
            if str(e) == 'There are no new harvesting jobs':
                pass

    def _gather_queue(self, num_jobs=1):
        for job in xrange(num_jobs):
            # Pop one item off the queue (the job id) and run the callback
            reply = self.gather_consumer.basic_get(
                queue='ckan.harvest.gather.test')

            # Make sure something was sent to the gather queue
            assert reply[2], 'Empty gather queue'

            # Send the item to the gather callback, which will call the
            # harvester gather_stage
            queue.gather_callback(self.gather_consumer, *reply)

    def _fetch_queue(self, num_objects=1):
        for _object in xrange(num_objects):
            # Pop item from the fetch queues (object ids) and run the callback,
            # one for each object created
            reply = self.fetch_consumer.basic_get(
                queue='ckan.harvest.fetch.test')

            # Make sure something was sent to the fetch queue
            assert reply[2], 'Empty fetch queue, the gather stage failed'

            # Send the item to the fetch callback, which will call the
            # harvester fetch_stage and import_stage
            queue.fetch_callback(self.fetch_consumer, *reply)

    def _run_full_job(self, harvest_source_id, num_jobs=1, num_objects=1):
        # Create new job for the source
        self._create_harvest_job(harvest_source_id)

        # Run the job
        self._run_jobs(harvest_source_id)

        # Handle the gather queue
        self._gather_queue(num_jobs)

        # Handle the fetch queue
        self._fetch_queue(num_objects)


class TestGeocatHarvestFunctional(FunctionalHarvestTest):
    def _test_harvest_create(self, all_results_filename,
                             single_results_filenames, num_objects,
                             expected_packages, **kwargs):
        self._mock_csw_results(all_results_filename, single_results_filenames)

        harvest_source = self._get_or_create_harvest_source(**kwargs)

        self._run_full_job(harvest_source['id'], num_objects=num_objects)

        # Check that correct amount of datasets were created
        fq = "+type:dataset harvest_source_id:{0}".format(harvest_source['id'])
        results = h.call_action('package_search', {}, fq=fq)
        eq_(results['count'], expected_packages)

        return results

    def _mock_csw_results(self, all_results_filename, single_results_filenames):
        path = os.path.join(__location__, 'fixtures', all_results_filename)
        with open(path) as xml:
            all_results = xml.read()

        httpretty.register_uri(httpretty.POST, mock_url, body=all_results)

        responses = []
        for filename in single_results_filenames:
            path = os.path.join(__location__, 'fixtures', filename)
            with open(path) as xml:
                result = xml.read()
            responses.append(httpretty.Response(result))

        httpretty.register_uri(httpretty.GET, mock_url, responses=responses)

    def test_harvest_create_simple(self):
        self._test_harvest_create('response_all_results.xml',
                                  [
                                      'result_1.xml',
                                      'result_2.xml',
                                  ], 2, 2)

    def test_harvest_deleted_dataset(self):
        test_config_deleted = json.dumps({'delete_missing_datasets': True})

        # Import two datasets
        self._test_harvest_create('response_all_results.xml',
                                  [
                                      'result_1.xml',
                                      'result_2.xml',
                                  ], 2, 2, config=test_config_deleted)

        # Run jobs to mark the old job finished
        self._run_jobs()

        # Import again, this time with only one dataset
        results = self._test_harvest_create('response_just_one_result.xml',
                                            ['result_1.xml'], 3, 1,
                                            config=test_config_deleted)
        self._run_jobs()

        # Get the harvest source with the updated status
        harvest_source = self._get_or_create_harvest_source(config=test_config_deleted)

        last_job_status = harvest_source['status']['last_job']
        eq_(last_job_status['status'], 'Finished')

        error_count = len(last_job_status['object_error_summary'])
        eq_(error_count, 0)
