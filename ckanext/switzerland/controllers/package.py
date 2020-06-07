# encoding: utf-8

import logging
import os
import ckan.controllers.package as package
import ckanext.switzerland.helpers.backend as bh

log = logging.getLogger(__name__)


class OgdchPackageController(package.PackageController):

    def _search_template(self, package_type):
        return bh.ogdch_template_choice(
            template_frontend=os.path.join('package', 'search_ogdch.html'),
            template_backend=os.path.join('package', 'search.html')
        )
