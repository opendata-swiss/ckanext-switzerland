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

    def test_get_shacl_shape_file_path(self):
        shapefile = 'ech-0200.shacl.ttl'
        result = tk_dcat.get_shacl_shape_file_path(shapefile)
        self.assertEqual(
            result,
            os.path.join(
                self.shacldir, 'ech-0200.shacl.ttl')
        )
