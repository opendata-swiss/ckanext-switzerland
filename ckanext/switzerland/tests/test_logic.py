import json
import unittest
from mock import patch
from nose.tools import assert_equal, assert_raises
from nose.plugins.skip import SkipTest
from ckanext.harvest.tests.test_action import ActionBase, SOURCE_DICT
from ckanext.harvest.tests import factories
from ckan.plugins import toolkit
from ckan import model


class TestActions(ActionBase):
    def test_cleanup_harvestjobs_for_one_source(self):
        # prepare
        source = factories.HarvestSourceObj(**SOURCE_DICT.copy())
        job = factories.HarvestJobObj(source=source)
        dataset = ckan_factories.Dataset()
        object_ = factories.HarvestObjectObj(job=job, source=source,
                                             package_id=dataset['id'])

        # execute
        context = {'model': model, 'session': model.Session,
                   'ignore_auth': True, 'user': ''}
        """
        result = toolkit.get_action('harvest_source_job_history_clear')(
            context, {'id': source.id})

        # verify
        assert_equal(result, {'id': source.id})
        source = harvest_model.HarvestSource.get(source.id)
        assert source
        assert_equal(harvest_model.HarvestJob.get(job.id), None)
        assert_equal(harvest_model.HarvestObject.get(object_.id), None)
        dataset_from_db = model.Package.get(dataset['id'])
        assert dataset_from_db, 'is None'
        assert_equal(dataset_from_db.id, dataset['id'])
        """

    def test_cleanup_harvestjobs_for_all_sources(self):
        # prepare
        data_dict = SOURCE_DICT.copy()
        source_1 = factories.HarvestSourceObj(**data_dict)
        data_dict['name'] = 'another-source'
        data_dict['url'] = 'http://another-url'
        source_2 = factories.HarvestSourceObj(**data_dict)

        job_1 = factories.HarvestJobObj(source=source_1)
        dataset_1 = ckan_factories.Dataset()
        object_1_ = factories.HarvestObjectObj(job=job_1, source=source_1,
                                             package_id=dataset_1['id'])
        job_2 = factories.HarvestJobObj(source=source_2)
        dataset_2 = ckan_factories.Dataset()
        object_2_ = factories.HarvestObjectObj(job=job_2, source=source_2,
                                             package_id=dataset_2['id'])

        # execute
        context = {'model': model, 'session': model.Session,
                   'ignore_auth': True, 'user': ''}
        """ 
        result = toolkit.get_action('harvest_sources_job_history_clear')(
            context, {})

        # verify
        assert_equal(
            sorted(result),
            sorted([{'id': source_1.id}, {'id': source_2.id}]))
        source_1 = harvest_model.HarvestSource.get(source_1.id)
        assert source_1
        assert_equal(harvest_model.HarvestJob.get(job_1.id), None)
        assert_equal(harvest_model.HarvestObject.get(object_1_.id), None)
        dataset_from_db_1 = model.Package.get(dataset_1['id'])
        assert dataset_from_db_1, 'is None'
        assert_equal(dataset_from_db_1.id, dataset_1['id'])
        source_2 = harvest_model.HarvestSource.get(source_1.id)
        assert source_2
        assert_equal(harvest_model.HarvestJob.get(job_2.id), None)
        assert_equal(harvest_model.HarvestObject.get(object_2_.id), None)
        dataset_from_db_2 = model.Package.get(dataset_2['id'])
        assert dataset_from_db_2, 'is None'
        assert_equal(dataset_from_db_2.id, dataset_2['id'])
        """
