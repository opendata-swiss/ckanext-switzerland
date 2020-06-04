import logging
from ckan.plugins.toolkit import redirect_to, abort
from ckan.logic import get_action, NotFound
from ckan.common import _
from ckan.lib.base import BaseController

log = logging.getLogger(__name__)


class OgdchPermaController(BaseController):
    """
    This controller handles the permalinks
    """

    def read(self, id):
        """
        This action redirects requests to /perma/{identifier} to
        the corresponding /dataset/{slug} route
        """
        try:
            dataset = get_action('ogdch_dataset_by_identifier')(
                {'for_view': True},
                {'identifier': id}
            )
            # redirect to dataset detail page
            redirect_to('dataset_read', id=dataset['name'])
        except NotFound:
            abort(404, _('Dataset not found'))
