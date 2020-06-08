# -*- coding: utf-8 -*-
"""Tests for helpers.py."""
from nose.tools import *  # noqa
import mock
import ckanext.switzerland.helpers.terms_of_use as term
import ckanext.switzerland.helpers.localize as loc
import ckanext.switzerland.helpers.frontend as fh
import sys
from copy import deepcopy
import unittest


class TestHelpers(unittest.TestCase):
    def test_simplify_terms_of_use_open(self):
        term_id = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        result = term.simplify_terms_of_use(term_id)
        self.assertEquals(term_id, result)

    def test_simplify_terms_of_use_closed(self):
        term_id = 'NonCommercialNotAllowed-CommercialAllowed-ReferenceNotRequired'  # noqa
        result = term.simplify_terms_of_use(term_id)
        self.assertEquals('ClosedData', result)
