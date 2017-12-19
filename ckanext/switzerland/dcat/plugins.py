from ckanext.dcat.plugins import DCATPlugin
from ckan import plugins
import os
import sys


class OgdchDcatPlugin(DCATPlugin):
    plugins.implements(plugins.ITranslation)

    # ITranslation
    def i18n_directory(self):
        '''Change the directory of the *.mo translation files

        The default implementation assumes the plugin is
        ckanext/myplugin/plugin.py and the translations are stored in
        i18n/
        '''
        # assume plugin is called ckanext.<myplugin>.<...>.PluginClass
        extension_module_name = 'ckanext.dcat'
        module = sys.modules[extension_module_name]
        return os.path.join(os.path.dirname(module.__file__), 'i18n')

    def after_show(self, context, data_dict):
        """
        Override after_show from ckanext_dcat as the set_titles() here
        destroyed our custom theme
        """
        pass
