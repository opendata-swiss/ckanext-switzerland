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
