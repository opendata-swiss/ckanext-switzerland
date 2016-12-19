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
        return

    def tearDown(self):
        return

    def test_prepare_resource_format(self):
        ogdch_language_plugin = plugin.OgdchLanguagePlugin()

        resource_without_any_formats = {
            'download_url': None,
            'media_type': None,
            'format': None
        }
        resource_without_any_formats_cleaned = ogdch_language_plugin._prepare_resource_format(resource_without_any_formats.copy())
        self.assertIsNone(resource_without_any_formats_cleaned['format'])

        resource_with_invalid_format = {
            'download_url': None,
            'media_type': None,
            'format': 'catgif'
        }
        resource_with_invalid_format_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_invalid_format.copy())
        self.assertIsNone(resource_with_invalid_format_cleaned['format'])

        resource_with_valid_format = {
            'download_url': None,
            'media_type': None,
            'format': 'xml'
        }
        resource_with_valid_format_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_valid_format.copy())
        self.assertEquals('XML', resource_with_valid_format_cleaned['format'])

        resource_with_invalid_media_type = {
            'download_url': None,
            'media_type': 'cat/gif',
            'format': 'gif'
        }
        resource_with_invalid_media_type_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_invalid_media_type.copy())
        self.assertIsNone(resource_with_invalid_media_type_cleaned['format'])

        resource_with_valid_media_type_without_slash = {
            'download_url': None,
            'media_type': 'html',
            'format': 'xml'
        }
        resource_with_valid_media_type_without_slash_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_valid_media_type_without_slash.copy())
        self.assertEquals('HTML', resource_with_valid_media_type_without_slash_cleaned['format'])

        resource_with_valid_media_type_with_slash = {
            'download_url': None,
            'media_type': 'text/html',
            'format': 'xml'
        }
        resource_with_valid_media_type_with_slash_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_valid_media_type_with_slash.copy())
        self.assertEquals('HTML', resource_with_valid_media_type_with_slash_cleaned['format'])

        resourse_with_download_url_without_extension = {
            'download_url': 'http://download.url',
            'media_type': 'text/xml',
            'format': 'html'
        }
        resourse_with_download_url_without_extension_cleaned = ogdch_language_plugin._prepare_resource_format(resourse_with_download_url_without_extension.copy())
        self.assertEquals('XML', resourse_with_download_url_without_extension_cleaned['format'])

        resourse_with_download_url_with_invalid_extension = {
            'download_url': 'http://download.url/cat.gif?param=1',
            'media_type': 'text/xml',
            'format': 'xml'
        }
        resourse_with_download_url_with_invalid_extension_cleaned = ogdch_language_plugin._prepare_resource_format(resourse_with_download_url_with_invalid_extension.copy())
        self.assertEquals('xml', resourse_with_download_url_with_invalid_extension_cleaned['format'])

        resourse_with_download_url_with_valid_extension = {
            'download_url': 'http://download.url/file.zip?param=1',
            'media_type': 'text/xml',
            'format': 'xml'
        }
        resourse_with_download_url_with_valid_extension_cleaned = ogdch_language_plugin._prepare_resource_format(resourse_with_download_url_with_valid_extension.copy())
        self.assertEquals('ZIP', resourse_with_download_url_with_valid_extension_cleaned['format'])

        resource_with_ods_vndoas_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'application/vnd.oas...'
        }
        resource_with_ods_vndoas_format_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_ods_vndoas_format.copy())
        self.assertEquals('ODS', resource_with_ods_vndoas_format_cleaned['format'])

        resource_with_pcaxis_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'pc-axis file'
        }
        resource_with_pcaxis_format_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_pcaxis_format.copy())
        self.assertEquals('PC-AXIS', resource_with_pcaxis_format_cleaned['format'])

        resource_with_rdf_sparql_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'Application/Sparql-...'
        }
        resource_with_rdf_sparql_format_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_rdf_sparql_format.copy())
        self.assertEquals('RDF', resource_with_rdf_sparql_format_cleaned['format'])

        resource_with_shapefile_esri_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'ESRI Shapefile'
        }
        resource_with_shapefile_esri_format_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_shapefile_esri_format.copy())
        self.assertEquals('SHAPEFILE', resource_with_shapefile_esri_format_cleaned['format'])

        resource_with_text_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'text (.txt)'
        }
        resource_with_text_format_cleaned = ogdch_language_plugin._prepare_resource_format(
            resource_with_text_format.copy())
        self.assertEquals('TXT', resource_with_text_format_cleaned['format'])

        resource_with_comma_format = {
            'download_url': 'http://download.url',
            'media_type': None,
            'format': 'comma ...'
        }
        resource_with_comma_format_cleaned = ogdch_language_plugin._prepare_resource_format(
            resource_with_comma_format.copy())
        self.assertEquals('CSV', resource_with_comma_format_cleaned['format'])
