import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons

from ckanext.switzerland import validators


LANGUAGE_PRIORITIES = ['de', 'en', 'fr', 'it'] 

class OgdchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
    
    # IValidators

    def get_validators(self):
        return {
            'multiple_text': validators.multiple_text,
            'multiple_text_output': validators.multiple_text_output,
            'list_of_dicts': validators.list_of_dicts,
            }


class OgdchPackagePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def before_view(self, data_dict):
        desired_lang_code = pylons.request.environ['CKAN_LANG']
        for key, value in data_dict.iteritems():
            if isinstance(value, dict):
                data_dict[key] = self.get_language_value(value, desired_lang_code, default_value=value)
        for resource in data_dict['resources']:
            if not resource['name'] and resource['title']:
                resource['name'] = resource['title']
            for key, value in resource.iteritems():
                if isinstance(value, dict):
                    resource[key] = self.get_language_value(value, desired_lang_code, default_value=value)
        return data_dict

    def get_language_value(self, lang_dict, desired_lang_code, default_value=''):
        try:
            if lang_dict[desired_lang_code]:
                return lang_dict[desired_lang_code]
        except KeyError:
            pass

        lang_idx = LANGUAGE_PRIORITIES.index(desired_lang_code)
        for i in range(0,len(LANGUAGE_PRIORITIES)):
            try:
                # choose next language according to priority
                lang_code = LANGUAGE_PRIORITIES[lang_idx-i]
                if str(lang_dict[lang_code]):
                    return lang_dict[lang_code]
            except (KeyError, IndexError, ValueError):
                continue
        return default_value
