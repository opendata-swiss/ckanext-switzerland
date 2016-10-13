"""Tests for helpers.py."""
from nose.tools import *  # noqa
import mock
import ckanext.switzerland.helpers as helpers
import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

class TestHelpers(unittest.TestCase):
    def test_simplify_terms_of_use_open(self):
        term_id = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired'
        result = helpers.simplify_terms_of_use(term_id)
        self.assertEquals(term_id, result)

    def test_simplify_terms_of_use_closed(self):
        term_id = 'NonCommercialNotAllowed-CommercialAllowed-ReferenceNotRequired'
        result = helpers.simplify_terms_of_use(term_id)
        self.assertEquals('ClosedData', result)

    def test_get_localized_value_dict(self):
        lang_dict = {
            'de': 'DE value',
            'fr': 'FR value',
            'it': 'IT value',
            'en': 'EN value',
        }
        result = helpers.get_localized_value(lang_dict, 'de')
        self.assertEquals(lang_dict['de'], result)

    def test_get_localized_value_fallback(self):
        lang_dict = {
            'de': 'DE value',
            'fr': 'FR value',
            'it': 'IT value',
            'en': '',
        }
        result = helpers.get_localized_value(lang_dict, 'en')
        # if en does not exist, fallback to de
        self.assertEquals(lang_dict['de'], result)

    @mock.patch('pylons.request')
    def test_get_localized_value_no_lang(self, mock_request):
        mock_request.environ = {'CKAN_LANG': 'fr'}

        lang_dict = {
            'de': 'DE value',
            'fr': 'FR value',
            'it': 'IT value',
            'en': 'EN value',
        }
        result = helpers.get_localized_value(lang_dict)
        self.assertEquals(lang_dict['fr'], result)

    def test_get_localized_value_invalid_dict(self):
        test_dict = {'test': 'dict'}
        result = helpers.get_localized_value(test_dict)
        self.assertEquals(test_dict, result)
