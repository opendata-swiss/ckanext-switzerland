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


class TestDcatShaclHelpers(object):

    def test_something_more(self):

        assert(1==2)
