# -*- coding: utf-8 -*-

import os

import unittest
import rdflib
from rdflib.namespace import NamespaceManager

from ckanext.switzerland.dcat.profiles import SHACL


class TestSwissShaclProfileParsing(unittest.TestCase):

    def setUp(self):
        resultfile = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            'shaclresult.ttl')
        self.r = rdflib.Graph()
        self.r.parse(resultfile, format='turtle')
        self.r.bind('sh', SHACL)
        self.r.namespace_manager = NamespaceManager(self.r)

    def test_shacl_result_reading(self):
        self.assertEqual(len(self.r), 804)

    def test_shaclresults_grouped_by_node(self):
        result = self.r.shaclresults_grouped_by_node(self)
        self.assertEqual(len(result.keys()), 16)
        self.assertListEqual(
            result.keys(),
            [u'https://data.bs.ch/api/v2/catalog/datasets/100004/exports/json',
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
             u'https://data.bs.ch/api/v2/catalog/datasets/100005/exports/json']
        )