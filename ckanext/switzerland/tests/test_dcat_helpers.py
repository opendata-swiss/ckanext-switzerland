# -*- coding: utf-8 -*-

import unittest
import os

import ckanext.switzerland.dcat.helpers as tk_dcat


class TestDcatShaclHelpers(unittest.TestCase):

    def setUp(self):
        self.resultdir = tk_dcat.get_shacl_resultdir_from_config()
        self.shacldir = tk_dcat.SHACL_SHAPES_DIR

    def test_get_shacl_command_from_config(self):
        result = tk_dcat.get_shacl_command_from_config()
        self.assertEquals(result.split('/')[-1], 'shacl')

    def test_get_shacl_resultdir_from_config(self):
        result = tk_dcat.get_shacl_resultdir_from_config()
        self.assertIsNotNone(result)

    def test_get_shacl_shapedir(self):
        result = tk_dcat.get_shacl_shapedir()
        self.assertIsNotNone(result)

    def test_get_shacl_data_file_path(self):
        harvest_source_id = '93488cd9'
        harvest_job_id = '908cd623'
        page_count = 3
        format = 'ttl'
        result = tk_dcat.get_shacl_data_file_path(
            harvest_source_id,
            harvest_job_id, page_count, format)
        self.assertEqual(
            result,
            os.path.join(
                self.resultdir, '93488cd9', '908cd623',
                'page-3.ttl' )
        )

    def test_get_shacl_result_file_path(self):
        harvest_source_id = '93488cd9'
        harvest_job_id = '908cd623'
        page_count = 3
        shapefile = 'ech-0200.shacl.ttl'
        format = 'ttl'
        result = tk_dcat.get_shacl_result_file_path(
            harvest_source_id,
            harvest_job_id, page_count, shapefile, format)
        self.assertEqual(
            result,
            os.path.join(
                self.resultdir, '93488cd9', '908cd623',
                'ech-0200.page-3.ttl')
        )

    def test_get_shacl_shape_file_path(self):
        shapefile = 'ech-0200.shacl.ttl'
        result = tk_dcat.get_shacl_shape_file_path(shapefile)
        self.assertEqual(
            result,
            os.path.join(
                self.shacldir, 'ech-0200.shacl.ttl')
        )

    def test_clean_shacl_dirs(self):
        harvest_source_id = '93488cd9'
        deleted_jobs_ids = ['12', '23']
        os.makedirs(os.path.join(self.resultdir, '93488cd9', '12'))
        os.makedirs(os.path.join(self.resultdir, '93488cd9', '23'))
        os.makedirs(os.path.join(self.resultdir, '93488cd9', '34'))
        os.makedirs(os.path.join(self.resultdir, '56778d34', '12'))
        tk_dcat.clean_shacl_result_dirs(
            harvest_source_id, deleted_jobs_ids)
        self.assertFalse(os.path.isdir(os.path.join(self.resultdir, '93488cd9', '12')))
        self.assertFalse(os.path.isdir(os.path.join(self.resultdir, '93488cd9', '23')))
        self.assertTrue(os.path.isdir(os.path.join(self.resultdir, '93488cd9', '34')))
        self.assertTrue(os.path.isdir(os.path.join(self.resultdir, '56778d34', '12')))
