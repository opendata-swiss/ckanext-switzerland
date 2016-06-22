from ckan.controllers.api import ApiController
from ckan.common import _, request
import ckan.lib.base as base
from ckan.logic import NotFound
from email.mime.text import MIMEText
from urlparse import urlparse

import ckan.plugins.toolkit as tk
import pylons
import json
import smtplib
import requests
import logging
log = logging.getLogger(__name__)


class DiscourseController(ApiController):

    # /api/ogdch_discourse_post_created/
    def post_created(self):
        '''Send a notification of a new post in a topic on discourse
        to the contact-points of the dataset.'''

        discourse_post = json.loads(request.body)

        ckan_site_url = urlparse(pylons.config.get('ckan.site_url', None))
        ckan_hostname = ckan_site_url.hostname

        discourse_topic_url = urlparse(discourse_post[1]['referrer'])
        discourse_topic_url_endpoint = discourse_topic_url.geturl() + '.json'
        discourse_topic = requests.get(
            discourse_topic_url_endpoint,
            verify=False).json()

        for link in discourse_topic['details']['links']:
            url = urlparse(link['url'])
            if link['domain'] == ckan_hostname and \
                    url.path.startswith('/dataset/'):
                dataset_url = link['url']
                package_id = dataset_url.split('/dataset/', 1)[1] \
                                        .replace('/', '')
                try:
                    package = tk.get_action('package_show')(
                        {'ignore_auth': True},
                        {'id': package_id}
                    )
                    self._notify_contactpoints(
                        discourse_topic_url,
                        dataset_url,
                        package
                    )
                except NotFound:
                    base.abort(
                        404,
                        _(
                            'The dataset {id} could not be found.'
                        ).format(id=id)
                    )

    def _notify_contactpoints(self, discourse_topic_url, dataset_url, package):

        smtp_host = pylons.config.get('smtp.server', None)
        smtp_port = pylons.config.get('smtp.host', None)
        from_mail = 'no-reply@opendata.swiss'

        for contact in package['contact_points']:
            receiver_mail = contact['email']
            receiver_name = contact['name']

            mail = 'Hello ' + receiver_name + '!\n\n'
            mail += 'A new post was created on Discourse at: '
            mail += discourse_topic_url.geturl() + '\n'
            mail += 'You receive this mail as a contact point of the dataset '
            mail += package['title']['en'] + ' at ' + dataset_url + ' \n'
            mail += 'To read the post follow this link: '
            mail += discourse_topic_url.geturl()

            msg = MIMEText(mail)
            msg['Subject'] = 'Discourse Notification'
            msg['From'] = from_mail
            msg['To'] = receiver_mail

            s = smtplib.SMTP(smtp_host, smtp_port)
            s.sendmail(from_mail, receiver_mail, msg.as_string())
            s.quit()
