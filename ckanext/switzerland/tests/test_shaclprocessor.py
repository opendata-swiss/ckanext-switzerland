# -*- coding: utf-8 -*-

import os

import unittest
import rdflib
from rdflib.namespace import NamespaceManager

from ckanext.switzerland.dcat.shaclprocessor import ShaclParser


class TestSwissShaclProfileParsing(unittest.TestCase):

    def setUp(self):
        page_count = 1
        harvest_source_id = '123'
        resultpath = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            'shaclresult.ttl')
        self.shaclparser = ShaclParser(resultpath, harvest_source_id)
        self.shaclparser.parse()

    def test_shaclresult_create(self):
        self.assertEqual(len(self.shaclparser.g), 804)

    def test_shaclresults_parse(self):
        error_count = 0
        for _error in self.shaclparser.shaclresults():
            error_count += 1
        self.assertEqual(error_count, 94)
