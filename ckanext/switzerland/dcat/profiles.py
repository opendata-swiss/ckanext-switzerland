import rdflib
from rdflib.namespace import Namespace, RDFS, RDF
from pprint import pprint

from datetime import datetime
import time

from ckanext.dcat.profiles import RDFProfile

from ckanext.switzerland.helpers import get_langs

import logging
log = logging.getLogger(__name__)

from pprint import pprint

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
SCHEMA = Namespace('http://schema.org/')
ODRS = Namespace('http://schema.theodi.org/odrs#')


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
                if lang not in lang_dict:
                    lang_dict[lang] = ''
        return lang_dict

    def _publishers(self, subject, predicate):

        publishers = []

        for agent in self.g.objects(subject, predicate):
            publisher = {'label': self._object_value(agent, RDFS.label)}
            publishers.append(publisher)

        return publishers

    def _relations(self, subject, predicate):

        relations = []

        for relation_node in self.g.objects(subject, predicate):
            relation = {'label': self._object_value(relation_node, RDFS.label), 'url': relation_node}
            relations.append(relation)

        return relations

    def _keywords(self, subject, predicate):

        keywords = {}

        for lang in get_langs():
            keywords[lang] = []

        for keyword_node in self.g.objects(subject, predicate):
            keywords[keyword_node.language].append(unicode(keyword_node))

        return keywords

    def _contact_points(self, subject, predicate):

        contact_points = []

        for contact_node in self.g.objects(subject, predicate):
            email = self._object_value(contact_node, VCARD.hasEmail)
            email_clean = email.replace('mailto:', '')
            contact = {'name': self._object_value(contact_node, VCARD.fn), 'email': email_clean}

            contact_points.append(contact)

        return contact_points

    def _temporals(self, subject, predicate):

        temporals = []

        for temporal_node in self.g.objects(subject, predicate):
            start_date = self._object_value(temporal_node, SCHEMA.startDate)
            end_date = self._object_value(temporal_node, SCHEMA.endDate)
            if start_date or end_date:
                temporals.append({'start_date': self._clean_datetime(start_date), 'end_date': self._clean_datetime(end_date)})

        return temporals

    def _clean_datetime(self, datetime_value):
        try:
            d = datetime.strptime(
                datetime_value[0:len('YYYY-MM-DD')],
                '%Y-%m-%d'
            )
            return int(time.mktime(d.timetuple()))
        except (ValueError, KeyError, TypeError, IndexError):
            raise ValueError("Could not parse datetime")

    def parse_dataset(self, dataset_dict, dataset_ref):  # noqa
        dataset_dict['temporals'] = []
        dataset_dict['tags'] = []
        dataset_dict['extras'] = []
        dataset_dict['resources'] = []
        dataset_dict['relations'] = []
        dataset_dict['see_alsos'] = []

        # Basic fields
        for key, predicate in (
                ('identifier', DCT.identifier),
                ('accrual_periodicity', DCT.accrualPeriodicity),
                ('spatial_uri', DCT.spatial),
                ('url', DCAT.landingPage),
                ):
            value = self._object_value(dataset_ref, predicate)
            if value:
                dataset_dict[key] = value

        # Timestamp fields
        for key, predicate in (
                ('issued', DCT.issued),
                ('modified', DCT.modified),
                ):
            value = self._object_value(dataset_ref, predicate)
            if value:
                dataset_dict[key] = self._clean_datetime(value)


        # Multilingual basic fields
        for key, predicate in (
                ('title', DCT.title),
                ('description', DCT.description),
                ):
            value = self._object_value(dataset_ref, predicate, multilang=True)
            if value:
                dataset_dict[key] = value

        # Tags
        keywords = self._object_value_list(dataset_ref, DCAT.keyword) or []
        for keyword in keywords:
            dataset_dict['tags'].append({'name': keyword})

        # Keywords
        dataset_dict['keywords'] = self._keywords(dataset_ref, DCAT.keyword)

        #  Lists
        for key, predicate in (
                ('language', DCT.language),
                ('theme', DCAT.theme),
                ):
            values = self._object_value_list(dataset_ref, predicate)
            if values:
                dataset_dict[key] = values

        # Contact details
        dataset_dict['contact_points'] = self._contact_points(dataset_ref, DCAT.contactPoint)

        # Publisher
        dataset_dict['publishers'] = self._publishers(dataset_ref, DCT.publisher)

        # Relations
        dataset_dict['relations'] = self._relations(dataset_ref, DCT.relation)

        # Temporal
        dataset_dict['temporals'] = self._temporals(dataset_ref, DCT.temporal)

        # References
        see_alsos  = self._object_value_list(dataset_ref, RDFS.seeAlso)
        for see_also in see_alsos:
            dataset_dict['see_alsos'].append({'dataset_identifier': see_also})

        # Dataset URI (explicitly show the missing ones)
        dataset_uri = (unicode(dataset_ref)
                       if isinstance(dataset_ref, rdflib.term.URIRef)
                       else None)
        dataset_dict['extras'].append({'key': 'uri', 'value': dataset_uri})

        # Resources
        for distribution in self._distributions(dataset_ref):

            resource_dict = {
                'media_type': None,
                'language': [],
            }

            #  Simple values
            for key, predicate in (
                    ('identifier', DCT.identifier),
                    ('format', DCT['format']),
                    ('mimetype', DCAT.mediaType),
                    ('media_type', DCAT.mediaType),
                    ('download_url', DCAT.downloadURL),
                    ('access_url', DCAT.accessURL),
                    ('rights', DCT.rights),
                    ):
                value = self._object_value(distribution, predicate)
                if value:
                    resource_dict[key] = value

            # Timestamp fields
            for key, predicate in (
                    ('issued', DCT.issued),
                    ('modified', DCT.modified),
                    ):
                value = self._object_value(distribution, predicate)
                if value:
                    resource_dict[key] = self._clean_datetime(value)

            # Multilingual fields
            for key, predicate in (
                    ('title', DCT.title),
                    ('description', DCT.description),
                    ):
                value = self._object_value(
                    distribution,
                    predicate,
                    multilang=True)
                if value:
                    resource_dict[key] = value

            resource_dict['url'] = (self._object_value(distribution,
                                                       DCAT.accessURL) or
                                    self._object_value(distribution,
                                                       DCAT.downloadURL))

            # languages
            for language in self._object_value_list(distribution, DCAT.language):
                resource_dict['language'].append(language)

            # byteSize
            byte_size = self._object_value_int(distribution, DCAT.byteSize)
            if byte_size is not None:
                resource_dict['byte_size'] = byte_size

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
