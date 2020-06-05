import unittest
import ckanext.switzerland.helpers.localize as localize
import ckanext.switzerland.helpers.helpers as h
import ckanext.switzerland.helpers.plugin_utils as pu



org = {'display_name': {u'fr': u'Office de sanite', u'de': u'Bundesamt f\xfcr Gesundheit',
                        u'en': u'Departement of Health', u'it': u'offici di sanitice'},
       'description': {u'fr': u'', u'de': u'', u'en': u'', u'it': u''}, 'image_display_url': u'', u'url': u'',
       'package_count': 3, 'created': '2015-11-04T15:13:10.945419', 'name': u'bundesamt-fur-gesundheit',
       'is_organization': True, 'state': u'active', 'image_url': u'',
       'revision_id': u'72693f68-2624-44f7-8cbd-054aaf8702dc', 'groups': [], 'type': u'organization',
       'title': {u'fr': u'Office de sanite', u'de': u'Bundesamt f\xfcr Gesundheit', u'en': u'Departement of Health',
                 u'it': u'offici di sanitice'}, u'political_level': u'confederation', 'num_followers': 0,
       'id': u'1caae51a-0ab6-4bee-8104-5716bbbf43ba', 'tags': [], 'approval_status': u'approved'}


class TestLanguageHelpers(unittest.TestCase):
    def setUp(self):
        self.multi_language_field_filled = {'de': 'Haus', 'en': 'house', 'fr': '', 'it': ''}
        self.multi_language_field_fr = {'de': '', 'en': 'house', 'fr': 'maison', 'it': ''}
        self.multi_language_field_en = {'de': '', 'en': 'house', 'fr': '', 'it': '?'}
        self.multi_language_field_it = {'de': '', 'en': '', 'fr': '', 'it': '?'}
        self.multi_language_field_empty = {'de': '', 'en': '', 'fr': '', 'it': ''}
        self.backup = 'Pferd'
        self.no_dict = 'some value'
        self.no_language_dict = {'de': 'Hallo', 'fr': 'Bonjour'}
        self.language_it = 'it'

    def test__localize_by_language_order(self):
        field_build = localize._localize_by_language_order(self.multi_language_field_filled, self.backup)
        field_expected = 'Haus'
        self.assertEqual(field_build, field_expected)

    def test__get_field_in_one_language_backup(self):
        field_build = localize._localize_by_language_order(self.multi_language_field_empty, self.backup)
        field_expected = 'Pferd'
        self.assertEqual(field_build, field_expected)

    def test__get_field_in_one_language_fr(self):
        field_build = localize._localize_by_language_order(self.multi_language_field_fr, self.backup)
        field_expected = 'maison'
        self.assertEqual(field_build, field_expected)

    def test__get_field_in_one_language_en(self):
        field_build = localize._localize_by_language_order(self.multi_language_field_en, self.backup)
        field_expected = 'house'
        self.assertEqual(field_build, field_expected)

    def test__get_field_in_one_language_it(self):
        field_build = localize._localize_by_language_order(self.multi_language_field_it, self.backup)
        field_expected = '?'
        self.assertEqual(field_build, field_expected)

    def test_get_localized_value_no_dict(self):
        field_build = localize.get_localized_value(self.no_language_dict)
        field_expected = self.no_language_dict
        self.assertEqual(field_build, field_expected)

    def test_get_localized_value_no_language_dict(self):
        field_build = localize.get_localized_value(self.no_language_dict)
        field_expected = self.no_language_dict
        self.assertEqual(field_build, field_expected)

    def test_get_localized_value_it(self):
        field_build = localize.get_localized_value(self.multi_language_field_en, desired_lang_code=self.language_it)
        field_expected = '?'
        self.assertEqual(field_build, field_expected)

    def test_get_localized_value_fallback_lang(self):
        field_build = localize.get_localized_value(self.multi_language_field_filled, desired_lang_code=self.language_it)
        field_expected = 'house'
        self.assertEqual(field_build, field_expected)

    def test_get_localized_value_fallback(self):
        field_build = localize.get_localized_value(self.multi_language_field_empty, desired_lang_code=self.language_it, default_value=self.backup)
        field_expected = self.backup
        self.assertEqual(field_build, field_expected)
