from ckanext.dcat.plugins import DCATPlugin


class OgdchDcatPlugin(DCATPlugin):
    def after_show(self, context, data_dict):
        """
        Override after_show from ckanext_dcat as the set_titles() here
        destroyed our custom theme
        """
        pass
