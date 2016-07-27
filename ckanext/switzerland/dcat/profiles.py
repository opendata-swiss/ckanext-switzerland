import rdflib
from rdflib.namespace import Namespace, RDFS
from pprint import pprint

from ckanext.dcat.profiles import RDFProfile

from ckanext.switzerland.helpers import get_langs

import logging
log = logging.getLogger(__name__)


DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")


class SwissDCATAPProfile(RDFProfile):
    '''
    An RDF profile for the DCAT-AP Switzerland recommendation for data portals

    It requires the European DCAT-AP profile (`euro_dcat_ap`)
    '''
    def _object_value(self, subject, predicate, multilang=False):
        '''
        Given a subject and a predicate, returns the value of the object

        Both subject and predicate must be rdflib URIRef or BNode objects

        If found, the unicode representation is returned, else None
        '''
        lang_dict = {}
        for o in self.g.objects(subject, predicate):
            if multilang and o.language:
                lang_dict[o.language] = unicode(o)
            else:
                return unicode(o)
        if multilang:
            # when translation does not exist, create an empty one
            for lang in get_langs():
                if not lang in lang_dict:
                    lang_dict[lang] = ''
            return lang_dict
        else:
            return None

    def _publisher(self, subject, predicate):
        '''
        Returns a dict with details about a dct:publisher entity, a rdfs:label

        Both subject and predicate must be rdflib URIRef or BNode objects

        Example:
        <dct:publisher>
          <rdf:Description rdf:about="http://termdat/some-org">
            <rdfs:label>SomeOrg Inc.</rdfs:label>
          </rdf:Description>
        </dct:publisher>

        {
            'uri': 'http://termdat/some-org',
            'name': 'SomeOrg Inc.',
            'email': None,
            'url': None,
            'type': None
        }

        Returns keys for uri, name, email, url and type with the values set to
        None if they could not be found
        '''

        publisher = {}

        for agent in self.g.objects(subject, predicate):

            publisher['uri'] = (str(agent) if isinstance(agent,
                                rdflib.term.URIRef) else None)

            publisher['name'] = self._object_value(agent, RDFS.label)
            publisher['email'] = None
            publisher['url'] = None
            publisher['type'] = None

        return publisher

    def _contact_details(self, subject, predicate):
        '''
        Returns a dict with details about a vcard expression

        Both subject and predicate must be rdflib URIRef or BNode objects

        Returns keys for uri, name and email with the values set to
        None if they could not be found
        '''

        contact = {}

        for agent in self.g.objects(subject, predicate):

            contact['uri'] = (str(agent) if isinstance(agent,
                              rdflib.term.URIRef) else None)

            contact['name'] = self._object_value(agent, VCARD.fn)

            contact['email'] = self._object_value(agent, VCARD.hasEmail)

        return contact

    def parse_dataset(self, dataset_dict, dataset_ref):  # noqa
        dataset_dict['temporals'] = None
        dataset_dict['tags'] = []
        dataset_dict['extras'] = []
        dataset_dict['resources'] = []
        dataset_dict['relations'] = []  # TODO: handle relations
        dataset_dict['see_alsos'] = []  # TODO: handle see_alsos

        # Basic fields
        for key, predicate in (
                ('issued', DCT.issued),
                ('modified', DCT.modified),
                ('identifier', DCT.identifier),
                ('frequency', DCT.accrualPeriodicity),
                ('spatial_uri', DCT.spatial),
                ('url', DCAT.landingPage),
                ):
            value = self._object_value(dataset_ref, predicate)
            if value:
                dataset_dict[key] = value

        # Multilingual basic fields
        for key, predicate in (
                ('title', DCT.title),
                ('notes', DCT.description),
                ):
            value = self._object_value(dataset_ref, predicate, multilang=True)
            if value:
                dataset_dict[key] = value

        # Tags
        keywords = self._object_value_list(dataset_ref, DCAT.keyword) or []
        for keyword in keywords:
            dataset_dict['tags'].append({'name': keyword})

        #  Lists
        for key, predicate in (
                ('language', DCT.language),
                ('theme', DCAT.theme),
                ):
            values = self._object_value_list(dataset_ref, predicate)
            if values:
                dataset_dict[key] = values

        # Contact details
        contact = self._contact_details(dataset_ref, DCAT.contactPoint)
        dataset_dict['contact_points'] = [contact]

        # Publisher
        publisher = self._publisher(dataset_ref, DCT.publisher)
        dataset_dict['publishers'] = [{'label': publisher.get('name')}]

        # Temporal
        start, end = self._time_interval(dataset_ref, DCT.temporal)
        if start:
            dataset_dict['extras'].append(
                {'key': 'temporal_start', 'value': start})
        if end:
            dataset_dict['extras'].append(
                {'key': 'temporal_end', 'value': end})

        # Dataset URI (explicitly show the missing ones)
        dataset_uri = (unicode(dataset_ref)
                       if isinstance(dataset_ref, rdflib.term.URIRef)
                       else None)
        dataset_dict['extras'].append({'key': 'uri', 'value': dataset_uri})

        # Resources
        for distribution in self._distributions(dataset_ref):

            resource_dict = {'media_type': None}

            #  Simple values
            for key, predicate in (
                    ('format', DCT['format']),
                    ('mimetype', DCAT.mediaType),
                    ('media_type', DCAT.mediaType),
                    ('download_url', DCAT.downloadURL),
                    ('access_url', DCAT.accessURL),
                    ('issued', DCT.issued),
                    ('modified', DCT.modified),
                    ('rights', DCT.rights),
                    ('license', DCT.license),
                    ):
                value = self._object_value(distribution, predicate)
                if value:
                    resource_dict[key] = value

            # Multilingual fields
            for key, predicate in (
                    ('title', DCT.title),
                    ('description', DCT.description),
                    ):
                value = self._object_value(
                    dataset_ref,
                    predicate,
                    multilang=True)
                if value:
                    dataset_dict[key] = value

            resource_dict['url'] = (self._object_value(distribution,
                                                       DCAT.accessURL) or
                                    self._object_value(distribution,
                                                       DCAT.downloadURL))

            size = self._object_value_int(distribution, DCAT.byteSize)
            if size is not None:
                    resource_dict['size'] = size

            # Distribution URI (explicitly show the missing ones)
            resource_dict['uri'] = (unicode(distribution)
                                    if isinstance(distribution,
                                                  rdflib.term.URIRef)
                                    else None)

            dataset_dict['resources'].append(resource_dict)

        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        pprint(dataset_dict)
        log.debug(dataset_dict)
