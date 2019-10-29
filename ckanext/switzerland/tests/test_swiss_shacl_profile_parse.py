# -*- coding: utf-8 -*-

import os
from datetime import datetime

import nose
import rdflib

from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF

try:
    from ckan.tests import helpers
except ImportError:
    from ckan.new_tests import helpers

from ckanext.dcat.processors import RDFParser
from ckanext.switzerland.dcat.profiles import (DCAT, DCT)

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class BaseParseTest(object):

    def _get_file_contents(self, file_name):
        path = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            file_name)
        with open(path, 'r') as f:
            return f.read()


class TestSwissShaclProfileParsing(BaseParseTest):

    def setup(self):
        self.r = rdflib.Graph()
        self.r = rdflib.parse(file, format='turtle')

        contents = self._get_file_contents('1901.xml')

        assert(1==1)