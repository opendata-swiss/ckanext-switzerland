# -*- coding: utf-8 -*-

import os
from datetime import datetime

import nose

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

    def _extras(self, dataset):
        extras = {}
        for extra in dataset.get('extras'):
            extras[extra['key']] = extra['value']
        return extras

    def _get_file_contents(self, file_name):
        path = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            file_name)
        with open(path, 'r') as f:
            return f.read()



class TestSwissShaclProfileParsing(BaseParseTest):

    def test_something(self):

        assert(1==1)
