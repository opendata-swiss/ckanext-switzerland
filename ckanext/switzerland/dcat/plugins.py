from ckanext.dcat.plugins import DCATPlugin
from ckan import plugins
import os

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


class OgdchDcatPlugin(DCATPlugin):
    plugins.implements(plugins.ITranslation)

    # ITranslation
    def i18n_directory(self):
        '''Change the directory of the *.mo translation files

        The default implementation assumes the plugin is
        ckanext/myplugin/plugin.py and the translations are stored in
        i18n/

        Due to this issue (https://github.com/ckan/ckanext-dcat/issues/107)
        we need to override the ckanext-dcat-i18n-path relative to the
        location of this file.
        '''
        return os.path.join(
            __location__,
            '..',
            '..',
            '..',
            '..',
            'ckanext-dcat',
            'ckanext',
            'dcat',
            'i18n'
        )

    def after_show(self, context, data_dict):
        """
        Override after_show from ckanext_dcat as the set_titles() here
        destroyed our custom theme
        """
        pass
