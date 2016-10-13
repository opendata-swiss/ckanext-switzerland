"""Tests for plugin.py."""
import ckanext.switzerland.plugin as plugin
from nose.tools import *  # noqa
import mock
import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

class TestPlugin(unittest.TestCase):
    def setUp(self):
        self.pkg_dict = {
            'resources': [
                {
                    'format': 'XML'
                },
                {
                    'format': 'unknown_format'
                }
            ]
        }

    def tearDown(self):
        self.pkg_dict = None

    def test_prepare_resources_format(self):
        ogdch_language_plugin = plugin.OgdchLanguagePlugin()

        pkg_dict_cleaned_formats = ogdch_language_plugin._prepare_resources_format(self.pkg_dict.copy())
        self.assertEquals(pkg_dict_cleaned_formats['resources'][0]['format'], self.pkg_dict['resources'][0]['format'])
        self.assertIsNone(pkg_dict_cleaned_formats['resources'][1]['format'])
