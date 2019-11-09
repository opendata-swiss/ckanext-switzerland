# -*- coding: utf-8 -*-

import os
import unittest
from datetime import datetime

import nose

import ckanext.switzerland.dcat.helpers as tk_dcat

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class TestHelpers(unittest.TestCase):
    def test_get_shacl_page_identifier(self):
        page_count = 2
        result = tk_dcat._get_shacl_page_identifier(page_count)
        self.assertEquals(result, 'page-2')

    def test_get_shacl_shape_identifier(self):
        shacl_file = 'ech-0200.shacl.ttl'
        result = tk_dcat._get_shacl_shape_identifier(shacl_file)
        self.assertEquals(result, 'ech-0200')

    def test_get_shacl_command_from_config(self):
        result = tk_dcat.get_shacl_command_from_config()
        self.assertEquals(result.split('/')[-1], 'shacl')

