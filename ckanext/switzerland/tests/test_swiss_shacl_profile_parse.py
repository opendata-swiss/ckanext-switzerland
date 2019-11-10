# -*- coding: utf-8 -*-

import os

import unittest
import rdflib

from ckanext.switzerland.dcat.profiles import SHACL


class TestSwissShaclProfileParsing(unittest.TestCase):

    def setup(self):
        resultfile = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            'shacl-data.ttl')
        self.r = rdflib.Graph()
        self.r.parse(resultfile, format='turtle')
        self.r.bind('sh', SHACL)
        print("hello from setup")
        print(len(self.r))
        self.r.namespace_manager = rdflib.NamespaceManager(self.r)

    def test_len_shacl_result(self):
        self.assertEqual(len(self.r), 58)