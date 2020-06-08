# -*- coding: utf-8 -*-
"""Tests for helpers.py."""
from nose.tools import *  # noqa
import mock
import ckanext.switzerland.helpers.terms_of_use as term
import ckanext.switzerland.helpers.localize as loc
import ckanext.switzerland.helpers.frontend as fh
from copy import deepcopy
import unittest

organizations = [{'children': [],
                  'highlighted': False,
                  'id': u'7dbaad15-597f-499c-9a72-95de38b95cad',
                  'name': u'swiss-library',
                  'title': u'{"fr": "AAAAA (FR)", "de": "bbbbb (DE)", "en": "ààààà (EN)", "it": "ZZZZZ (IT)"}'},  # noqa
                 {'children': [],
                  'highlighted': False,
                  'id': u'51941490-5ade-4d06-b708-ff04279ce550',
                  'name': u'italian-library',
                  'title': u'{"fr": "YYYYY (FR)", "de": "ZZZZZ (DE)", "en": "üüüüü (EN)", "it": "AAAAA (IT)"}'},  # noqa
                 {'children': [{'children': [],
                                'highlighted': False,
                                'id': u'589ff525-be2f-4059-bea4-75c92739dfe9',
                                'name': u'child-swiss-library',
                                'title': u'{"fr": "AAAAA (FR)", "de": "yyyyy (DE)", "en": "zzzzz (EN)", "it": "BBBBB (IT)"}'},  # noqa
                               {'children': [],
                                'highlighted': False,
                                'id': u'2c559631-e174-4e9f-8c2a-940a08371340',
                                'name': u'child-italian-library',
                                'title': u'{"fr": "YYYYY (FR)", "de": "BBBBB (DE)", "en": "ööööö (EN)", "it": "ZZZZZ (IT)"}'}],  # noqa
                  'highlighted': False,
                  'id': u'73124d1e-c2aa-4d20-a42d-fa71b8946e93',
                  'name': u'swisstopo',
                  'title': u'{"fr": "Swisstopo FR", "de": "Swisstopo DE", "en": "ÉÉÉÉÉ (EN)", "it": "Swisstopo IT"}'}]  # noqa

organization_title = u'{"fr": "Swisstopo FR", "de": "Swisstopo DE", "en": "Swisstopo EN", "it": "Swisstopo IT"}'  # noqa

class TestHelpers(unittest.TestCase):
    def test_get_localized_value_from_dict(self):
        lang_dict = {
            'de': 'DE value',
            'fr': 'FR value',
            'it': 'IT value',
            'en': 'EN value',
        }
        result = loc.get_localized_value_from_dict(lang_dict, 'de')
        self.assertEquals(lang_dict['de'], result)

    def test_get_localized_value_from_dict_fallback(self):
        lang_dict = {
            'de': 'DE value',
            'fr': 'FR value',
            'it': 'IT value',
            'en': '',
        }
        result = loc.get_localized_value_from_dict(lang_dict, 'en')
        # if en does not exist, fallback to de
        self.assertEquals(lang_dict['de'], result)

    def test_parse_json_error_and_default_value(self):
        """if an error occurs the value should be returned as is"""
        value = u"{Hallo"
        default_value = "Hello world"
        self.assertEqual(loc.parse_json(value, default_value=default_value), default_value)

    def test_parse_json_with_error(self):
        """if an error occurs the default value should be returned"""
        value = u"{Hallo"
        self.assertEqual(loc.parse_json(value), value)

    def test_parse_json_without_error(self):
        """if an error occurs the default value should be returned"""
        value = '{"de": "Hallo", "it": "okay"}'
        value_as_dict = {"de": "Hallo", "it":"okay"}
        self.assertEqual(loc.parse_json(value), value_as_dict)
