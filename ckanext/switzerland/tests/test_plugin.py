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
        self.pkg_dict_full = {
            'license_title': None,
            'maintainer': 'asdf',
            'coverage': '',
            'issued': '2016-10-11T00:00:00',
            'private': False,
            'maintainer_email': 'asdf@asdf.ch',
            'num_tags': 0,
            'contact_points': [
              {
                'email': 'asdf@asdf.ch',
                'name': 'asdf'
              }
            ],
            'keywords': {
              'fr': [],
              'de': [],
              'en': [],
              'it': []
            },
            'temporals': {},
            'id': 'f630b8d8-e4f3-4e72-aa0b-38407469d169',
            'metadata_created': '2016-10-11T09:10:30.533809',
            'relationships_as_object': [],
            'display_name': {
              'fr': '',
              'de': '',
              'en': 'Format test',
              'it': ''
            },
            'metadata_modified': '2016-10-13T08:12:26.154445',
            'author': 'asdfasdf',
            'author_email': None,
            'relations': {},
            'state': 'active',
            'version': None,
            'spatial': '',
            'license_id': None,
            'type': 'dataset',
            'resources': [
                {
                    'coverage': '',
                    'cache_last_updated': None,
                    'issued': '2016-10-11T00:00:00',
                    'package_id': 'f630b8d8-e4f3-4e72-aa0b-38407469d169',
                    'webstore_last_updated': None,
                    'id': '739b57ed-6e21-4c42-9520-9decf1a0194f',
                    'size': None,
                    'display_name': {
                        'fr': '',
                        'de': '',
                        'en': 'no media_type',
                        'it': ''
                    },
                    'title': {
                        'fr': '',
                        'de': '',
                        'en': 'no media_type',
                        'it': ''
                    },
                    'download_url': '',
                    'state': 'active',
                    'media_type': '',
                    'hash': '',
                    'description': {
                        'fr': '',
                        'de': '',
                        'en': '',
                        'it': ''
                    },
                    'tracking_summary': {'total': 0, 'recent': 0},
                    'mimetype_inner': None,
                    'url_type': None,
                    'name': {
                        'fr': '',
                        'de': '',
                        'en': 'no media_type',
                        'it': ''
                    },
                    'mimetype': None,
                    'cache_url': None,
                    'language': [],
                    'license': '',
                    'created': '2016-10-13T08:12:26.207409',
                    'url': 'http://zugangs.url',
                    'rights': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
                    'modified': False,
                    'webstore_url': None,
                    'last_modified': None,
                    'position': 0,
                    'revision_id': '729747b4-bd8b-4d76-ac4a-06063d53ea1b',
                    'identifier': '',
                    'resource_type': None
                },
                {
                    'coverage': '',
                    'cache_last_updated': None,
                    'issued': '2016-10-11T00:00:00',
                    'package_id': 'f630b8d8-e4f3-4e72-aa0b-38407469d169',
                    'webstore_last_updated': None,
                    'id': '22a4d4bf-dea8-4727-b080-5859a49343e1',
                    'size': None,
                    'display_name': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url without extension',
                        'it': ''
                    },
                    'title': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url without extension',
                        'it': ''
                    },
                    'download_url': 'http://download.url',
                    'state': 'active',
                    'media_type': '',
                    'hash': '',
                    'description': {
                        'fr': '',
                        'de': '',
                        'en': '',
                        'it': ''
                    },
                    'tracking_summary': {
                        'total': 0,
                        'recent': 0
                    },
                    'mimetype_inner': None,
                    'url_type': None,
                    'name': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url without extension',
                        'it': ''
                    },
                    'mimetype': None,
                    'cache_url': None,
                    'language': [],
                    'license': '',
                    'created': '2016-10-13T08:12:26.207705',
                    'url': 'http://zugangs.url',
                    'rights': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
                    'modified': False,
                    'webstore_url': None,
                    'last_modified': None,
                    'position': 1,
                    'revision_id': '729747b4-bd8b-4d76-ac4a-06063d53ea1b',
                    'identifier': '',
                    'resource_type': None
                },
                {
                    'coverage': '',
                    'cache_last_updated': None,
                    'issued': '2016-10-11T00:00:00',
                    'package_id': 'f630b8d8-e4f3-4e72-aa0b-38407469d169',
                    'webstore_last_updated': None,
                    'id': '4ccae3a8-71e2-4a6e-97dd-9035aee16f6f',
                    'size': None,
                    'display_name': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url with extension',
                        'it': ''
                    },
                    'title': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url with extension',
                        'it': ''
                    },
                    'download_url': 'http://download.url/file.zip?bla=1',
                    'state': 'active',
                    'media_type': '',
                    'hash': '',
                    'description': {
                        'fr': '',
                        'de': '',
                        'en': '',
                        'it': ''
                    },
                    'format': None,
                    'tracking_summary': {
                        'total': 0,
                        'recent': 0
                    },
                    'mimetype_inner': None,
                    'url_type': None,
                    'name': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url with extension',
                        'it': ''
                    },
                    'mimetype': None,
                    'cache_url': None,
                    'language': [],
                    'license': '',
                    'created': '2016-10-13T08:12:26.207769',
                    'url': 'http://zugangs.url',
                    'rights': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
                    'modified': False,
                    'webstore_url': None,
                    'last_modified': None,
                    'position': 2,
                    'revision_id': '729747b4-bd8b-4d76-ac4a-06063d53ea1b',
                    'identifier': '',
                    'resource_type': None
                },
                {
                    'coverage': '',
                    'cache_last_updated': None,
                    'issued': '2016-10-11T00:00:00',
                    'package_id': 'f630b8d8-e4f3-4e72-aa0b-38407469d169',
                    'webstore_last_updated': None,
                    'id': '398df74b-5b88-460b-aa3b-6e6fb6a4ea29',
                    'size': None,
                    'display_name': {
                        'fr': '',
                        'de': '',
                        'en': 'media_type with slash given',
                        'it': ''
                    },
                    'title': {
                        'fr': '',
                        'de': '',
                        'en': 'media_type with slash given',
                        'it': ''
                    },
                    'download_url': '',
                    'state': 'active',
                    'media_type': 'text/html',
                    'hash': '',
                    'description': {
                        'fr': '',
                        'de': '',
                        'en': '',
                        'it': ''
                    },
                    'format': None,
                    'tracking_summary': {
                        'total': 0,
                        'recent': 0
                    },
                    'mimetype_inner': None,
                    'url_type': None,
                    'name': {
                        'fr': '',
                        'de': '',
                        'en': 'media_type with slash given',
                        'it': ''
                    },
                    'mimetype': None,
                    'cache_url': None,
                    'language': [],
                    'license': '',
                    'created': '2016-10-13T08:12:26.207826',
                    'url': 'http://zugangs.url',
                    'rights': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
                    'modified': False,
                    'webstore_url': None,
                    'last_modified': None,
                    'position': 3,
                    'revision_id': '729747b4-bd8b-4d76-ac4a-06063d53ea1b',
                    'identifier': '',
                    'resource_type': None
                },
                {
                    'coverage': '',
                    'cache_last_updated': None,
                    'issued': '2016-10-11T00:00:00',
                    'package_id': 'f630b8d8-e4f3-4e72-aa0b-38407469d169',
                    'webstore_last_updated': None,
                    'id': '3b0a8fe8-92bb-48ab-ad79-b54f88f39541',
                    'size': None,
                    'display_name': {
                        'fr': '',
                        'de': '',
                        'en': 'media_type without slash given',
                        'it': ''
                    },
                    'title': {
                        'fr': '',
                        'de': '',
                        'en': 'media_type without slash given',
                        'it': ''
                    },
                    'download_url': '',
                    'state': 'active',
                    'media_type': 'xlsx',
                    'hash': '',
                    'description': {
                        'fr': '',
                        'de': '',
                        'en': '',
                        'it': ''
                    },
                    'format': 'XLS',
                    'tracking_summary': {
                        'total': 0,
                        'recent': 0
                    },
                    'mimetype_inner': None,
                    'url_type': None,
                    'name': {
                        'fr': '',
                        'de': '',
                        'en': 'media_type without slash given',
                        'it': ''
                    },
                    'mimetype': None,
                    'cache_url': None,
                    'language': [],
                    'license': '',
                    'created': '2016-10-13T08:12:26.207878',
                    'url': 'http://zugangs.url',
                    'rights': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
                    'modified': False,
                    'webstore_url': None,
                    'last_modified': None,
                    'position': 4,
                    'revision_id': '729747b4-bd8b-4d76-ac4a-06063d53ea1b',
                    'identifier': '',
                    'resource_type': None
                },
                {
                    'coverage': '',
                    'cache_last_updated': None,
                    'issued': '2016-10-12T00:00:00',
                    'package_id': 'f630b8d8-e4f3-4e72-aa0b-38407469d169',
                    'webstore_last_updated': None,
                    'id': '7ac34092-9ef6-406c-a530-77e56c611acd',
                    'size': None,
                    'display_name': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url with extenstion and media_type given',
                        'it': ''
                    },
                    'title': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url with extenstion and media_type given',
                        'it': ''
                    },
                    'download_url': 'http://download.url/test.xml?asdfasdf=asdf',
                    'state': 'active',
                    'media_type': 'text/txt',
                    'hash': '',
                    'description': {
                        'fr': '',
                        'de': '',
                        'en': '',
                        'it': ''
                    },
                    'format': 'XML',
                    'tracking_summary': {
                        'total': 0,
                        'recent': 0
                    },
                    'mimetype_inner': None,
                    'url_type': None,
                    'name': {
                        'fr': '',
                        'de': '',
                        'en': 'download_url with extenstion and media_type given',
                        'it': ''
                    },
                    'mimetype': None,
                    'cache_url': None,
                    'language': [],
                    'license': '',
                    'created': '2016-10-13T08:12:26.207925',
                    'url': 'http://zugangs.url',
                    'rights': 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired',
                    'modified': False,
                    'webstore_url': None,
                    'last_modified': None,
                    'position': 5,
                    'revision_id': '729747b4-bd8b-4d76-ac4a-06063d53ea1b',
                    'identifier': '',
                    'resource_type': None
                }
            ],
            'publishers': [
                {
                    'label': 'asdfasdf'
                }
            ],
            'num_resources': 6,
            'description': {
                'fr': '',
                'de': '',
                'en': '',
                'it': ''
            },
            'tags': [],
            'title': {
                'fr': '',
                'de': '',
                'en': 'Format test',
                'it': ''
            },
            'language': []
        }

    def tearDown(self):
        self.pkg_dict_full = None

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
        self.assertEquals(resource_with_valid_format_cleaned['format'], 'XML')

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
        self.assertEquals(resource_with_valid_media_type_without_slash_cleaned['format'], 'HTML')

        resource_with_valid_media_type_with_slash = {
            'download_url': None,
            'media_type': 'text/html',
            'format': 'xml'
        }
        resource_with_valid_media_type_with_slash_cleaned = ogdch_language_plugin._prepare_resource_format(resource_with_valid_media_type_with_slash.copy())
        self.assertEquals(resource_with_valid_media_type_with_slash_cleaned['format'], 'HTML')

        resourse_with_download_url_without_extension = {
            'download_url': 'http://download.url',
            'media_type': 'text/xml',
            'format': 'html'
        }
        resourse_with_download_url_without_extension_cleaned = ogdch_language_plugin._prepare_resource_format(resourse_with_download_url_without_extension.copy())
        self.assertEquals(resourse_with_download_url_without_extension_cleaned['format'], 'XML')

        resourse_with_download_url_with_invalid_extension = {
            'download_url': 'http://download.url/cat.gif?param=1',
            'media_type': 'text/xml',
            'format': 'xml'
        }
        resourse_with_download_url_with_invalid_extension_cleaned = ogdch_language_plugin._prepare_resource_format(resourse_with_download_url_with_invalid_extension.copy())
        self.assertIsNone(resourse_with_download_url_with_invalid_extension_cleaned['format'])

        resourse_with_download_url_with_valid_extension = {
            'download_url': 'http://download.url/file.zip?param=1',
            'media_type': 'text/xml',
            'format': 'xml'
        }
        resourse_with_download_url_with_valid_extension_cleaned = ogdch_language_plugin._prepare_resource_format(resourse_with_download_url_with_valid_extension.copy())
        self.assertEquals(resourse_with_download_url_with_valid_extension_cleaned['format'], 'ZIP')
