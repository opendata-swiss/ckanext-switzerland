# -*- coding: utf-8 -*-

import os

import unittest
import rdflib
from rdflib.namespace import NamespaceManager

from ckanext.switzerland.dcat.shaclprocessor import ShaclParser


class TestSwissShaclProfileParsing(unittest.TestCase):

    def setUp(self):
        resultpath = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            'shaclresult.ttl')
        self.shaclresults = ShaclParser(resultpath)

    def test_shaclresult_create(self):
        self.assertEqual(len(self.shaclresults.g), 804)

    def test_shaclresults_grouped_by_node(self):
        error_dict = self.shaclresults.errors_grouped_by_node()
        self.assertEqual(len(error_dict.keys()), 16)
        self.assertSetEqual(
            set(error_dict.keys()),
            {u'https://data.bs.ch/api/v2/catalog/datasets/100004/exports/json',
             u'https://data.bs.ch/api/v2/catalog/datasets/100004',
             u'https://data.bs.ch/api/v2/catalog/datasets/100005',
             u'https://data.bs.ch/api/v2/catalog/datasets/100008',
             u'https://data.bs.ch/api/v2/catalog/datasets/100005/exports/geojson',
             u'https://data.bs.ch/api/v2/catalog/datasets/100008/exports/geojson',
             'catalog',
             u'https://data.bs.ch/api/v2/catalog/datasets/100004/exports/shp',
             u'https://data.bs.ch/api/v2/catalog/datasets/100008/exports/csv',
             u'https://data.bs.ch/api/v2/catalog/datasets/100008/exports/shp',
             u'https://data.bs.ch/api/v2/catalog/datasets/100005/exports/csv',
             u'https://data.bs.ch/api/v2/catalog/datasets/100004/exports/csv',
             u'https://data.bs.ch/api/v2/catalog/datasets/100005/exports/shp',
             u'https://data.bs.ch/api/v2/catalog/datasets/100004/exports/geojson',
             u'https://data.bs.ch/api/v2/catalog/datasets/100008/exports/json',
             u'https://data.bs.ch/api/v2/catalog/datasets/100005/exports/json'}
        )
        errors = sum([len(v) for k,v in error_dict.items()])
        self.assertEqual(errors, 94)
