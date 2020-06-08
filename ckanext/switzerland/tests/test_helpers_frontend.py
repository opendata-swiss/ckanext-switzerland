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

    @mock.patch('ckan.lib.i18n.get_lang', return_value='fr')
    def test_get_sorted_orgs_by_translated_title_fr(self, mock_get_lang):
        french_organizations = deepcopy(organizations)
        result_orgs = fh.get_sorted_orgs_by_translated_title(french_organizations)  # noqa

        for org in result_orgs:
            if org['children']:
                self.assertEqual(0, self.find_position_of_org(org['children'], u'AAAAA (FR)'))  # noqa
                self.assertEqual(1, self.find_position_of_org(org['children'], u'YYYYY (FR)'))  # noqa

        self.assertEqual(0, self.find_position_of_org(result_orgs, u'AAAAA (FR)'))  # noqa
        self.assertEqual(2, self.find_position_of_org(result_orgs, u'YYYYY (FR)'))  # noqa

    @mock.patch('ckan.lib.i18n.get_lang', return_value='it')
    def test_get_sorted_orgs_by_translated_title_it(self, mock_get_lang):
        italian_organizations = deepcopy(organizations)
        result_orgs = fh.get_sorted_orgs_by_translated_title(italian_organizations)  # noqa

        for org in result_orgs:
            if org['children']:
                self.assertEqual(0, self.find_position_of_org(org['children'], u'BBBBB (IT)'))  # noqa
                self.assertEqual(1, self.find_position_of_org(org['children'], u'ZZZZZ (IT)'))  # noqa

        self.assertEqual(2, self.find_position_of_org(result_orgs, u'ZZZZZ (IT)'))  # noqa
        self.assertEqual(0, self.find_position_of_org(result_orgs, u'AAAAA (IT)'))  # noqa

    @mock.patch('ckan.lib.i18n.get_lang', return_value='de')
    def test_get_sorted_orgs_by_translated_title_de(self, mock_get_lang):
        german_organizations = deepcopy(organizations)
        result_orgs = fh.get_sorted_orgs_by_translated_title(german_organizations)  # noqa

        for org in result_orgs:
            if org['children']:
                self.assertEqual(0, self.find_position_of_org(org['children'], u'BBBBB (DE)'))  # noqa
                self.assertEqual(1, self.find_position_of_org(org['children'], u'yyyyy (DE)'))  # noqa

        self.assertEqual(0, self.find_position_of_org(result_orgs, u'bbbbb (DE)'))  # noqa
        self.assertEqual(2, self.find_position_of_org(result_orgs, u'ZZZZZ (DE)'))  # noqa

    @mock.patch('ckan.lib.i18n.get_lang', return_value='en')
    def test_get_sorted_orgs_by_translated_title_en(self, mock_get_lang):
        english_organizations = deepcopy(organizations)
        result_orgs = fh.get_sorted_orgs_by_translated_title(english_organizations)  # noqa

        for org in result_orgs:
            if org['children']:
                self.assertEqual(0, self.find_position_of_org(org['children'], u'ööööö (EN)'))  # noqa
                self.assertEqual(1, self.find_position_of_org(org['children'], u'zzzzz (EN)'))  # noqa

        self.assertEqual(0, self.find_position_of_org(result_orgs, u'ààààà (EN)'))  # noqa
        self.assertEqual(1, self.find_position_of_org(result_orgs, u'ÉÉÉÉÉ (EN)'))  # noqa
        self.assertEqual(2, self.find_position_of_org(result_orgs, u'üüüüü (EN)'))  # noqa

    def find_position_of_org(self, org_list, title):
        index = next(
            (i for i, org in enumerate(org_list) if
             org['title'] == title),
            -1)
        return index
