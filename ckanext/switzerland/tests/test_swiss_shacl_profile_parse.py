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

    def test_len_shacl_result(self):
        self.assertEqual(len(self.r), 58)