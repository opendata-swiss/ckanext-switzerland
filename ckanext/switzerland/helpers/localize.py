from ckan.lib.helpers import lang

LANGUAGES = {'de', 'fr', 'it', 'en'}


def get_localized_value(lang_dict, desired_lang_code=None, default_value=''):
    """localizes language dict and
    returns value if it is no language dict"""
    if not isinstance(lang_dict, dict):
        return lang_dict
    elif set(lang_dict.keys()) != LANGUAGES:
        return lang_dict
    if not desired_lang_code:
        desired_lang_code = lang()
        desired_lang_value = lang_dict.get(desired_lang_code)
        if desired_lang_value:
            return desired_lang_value
    return _localize_by_language_order(lang_dict, default_value)


def _localize_by_language_order(multi_language_field, backup):
    """localizes language dict if no language is specified"""
    if multi_language_field.get('de'):
        return multi_language_field['de']
    elif multi_language_field.get('fr'):
        return multi_language_field['fr']
    elif multi_language_field.get('en'):
        return multi_language_field['en']
    elif multi_language_field.get('it'):
        return multi_language_field['it']
    else:
        return backup


def lang_to_string(data_dict, attribute):
    """make a long string with all 4 languages of an attribute"""
    value_dict = data_dict.get(attribute)
    value_string = ('%s - %s - %s - %s' % (
        value_dict.get('de', ''),
        value_dict.get('fr', ''),
        value_dict.get('it', ''),
        value_dict.get('en', '')
    ))
    return value_string
