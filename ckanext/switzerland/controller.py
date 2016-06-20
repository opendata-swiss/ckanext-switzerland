from ckan.controllers.api import ApiController
from ckan.common import _, c, request, response
from ckan.logic import NotFound
from ConfigParser import ConfigParser
from email.mime.text import MIMEText

import ckan.plugins.toolkit as tk
import pylons
import json
import smtplib
import logging
log = logging.getLogger(__name__)


class DiscourseController(ApiController):

    # /api/ogdch_discourse_post_created/
    def post_created(self):
        '''Render the config template with the first custom title.'''

        log.error(request.body)
        discourse = get_or_bust(request.body)

#         get_or_bust(request.body, 'url')

        # retrieve source url http://ogdch.dev/de/dataset/baustellen
        url = 'http://ogdch.dev/de/dataset/baustellen'

        if '/dataset/' in url:
            package_id = url.split('/dataset/', 1)[1].replace('/', '')
            log.error('Package ID: ' + package_id)
            try:
                pkg = tk.get_action('package_show')({'ignore_auth': True}, {'id': package_id})
                log.error(pkg)
                notifyContactPoints(discourse, pkg)
            except NotFound:
                abort(404, _('The dataset {id} could not be found.').format(id=id))

    def notifyContactPoints(discourse_msg, package):

        ckan_site_url = pylons.config.get('ckan.site_url', None)
        smtp_host = pylons.config.get('smtp.server', None)
        smtp_port = pylons.config.get('smtp.host', None)

        for contact in pkg['contact_points']:
            receiver_mail = contact['email']
            receiver_name = contact['name']

            dataset_url = ckan_site_url + '/dataset/' + pkg['name']

            mail = 'Hello ' + receiver_name + '!\n\n'
            mail += 'A new post was created on Discourse at: ' + discourse['referrer']
            mail += 'You receive this mail as a contact point of the dataset '
            mail += 'of ' + pkg[name] + ' at ' dataset_url + ' \n'
            mail += 'To read the post follow this link: ' + discourse['referrer']


            msg = MIMEText(mail)

            msg['Subject'] = 'Discourse Notification'
            msg['From'] = from_mail
            msg['To'] = receiver_mail

            s = smtplib.SMTP(smtp_host, smtp_port)
            s.sendmail(filename, filename, msg.as_string())
            s.quit()
