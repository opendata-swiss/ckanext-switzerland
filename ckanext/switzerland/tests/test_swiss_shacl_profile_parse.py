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


class TestSwissShaclProfileParsing(object):

    def setup(self):
        resultfile = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            'shacl-data.ttl')
        self.r = rdflib.Graph()
        self.r = rdflib.parse(resultfile, format='turtle')

    def test_something(self):
        assert(1==1)