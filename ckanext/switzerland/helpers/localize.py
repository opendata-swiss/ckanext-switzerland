"""
localization functions that don't need the request object
"""
import json

LANGUAGES = {'de', 'fr', 'it', 'en'}


def parse_json_attributes(ckan_dict):
    """turn attribute values from json
    to python structures"""
    for key, value in ckan_dict.iteritems():
        ckan_dict[key] = parse_json(value)
    return ckan_dict


def get_language_priorities():
    language_priorities = ['en', 'de', 'fr', 'it']
    return language_priorities


def parse_json(value, default_value=None):
    try:
        return json.loads(value)
    except (ValueError, TypeError, AttributeError):
        if default_value is not None:
            return default_value
        return value


def lang_to_string(data_dict, attribute):
    """make a long string with all 4 languages of an attribute"""
    value_dict = data_dict.get(attribute)
    return ('%s - %s - %s - %s' % (
        value_dict.get('de', ''),
        value_dict.get('fr', ''),
        value_dict.get('it', ''),
        value_dict.get('en', '')
    ))


def localize_ckan_sub_dict(ckan_dict, lang_code):
    """localize groups orgs and resources"""
    localized_dict = {}
    for k, v in ckan_dict.items():
        py_v = parse_json(v)
        localized_dict[k] = get_localized_value_from_dict(py_v, lang_code)
    return localized_dict


def get_localized_value_from_dict(value, lang_code, default=''):
    """localizes language dict and
    returns value if it is not a language dict"""
    if not isinstance(value, dict):
        return value
    elif set(value.keys()) != LANGUAGES:
        return value
    desired_lang_value = value.get(lang_code)
    if desired_lang_value:
        return desired_lang_value
    return _localize_by_language_order(value, default)


def get_localized_value_from_json(value, lang_code):
    """localizes language dict from json and
    returns value if it is not a language dict"""
    return get_localized_value_from_dict(parse_json(value), lang_code)


def _localize_by_language_order(multi_language_field, default=''):
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
        return default
