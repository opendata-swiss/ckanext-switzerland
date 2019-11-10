import rdflib
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDFS, RDF, SKOS

from datetime import datetime
from collections import defaultdict

from ckantoolkit import config

import re

from ckanext.dcat.profiles import RDFProfile, SchemaOrgProfile
from ckanext.dcat.utils import resource_uri, publisher_uri_from_dataset_dict
from ckan.lib.munge import munge_tag

from ckanext.switzerland.helpers import get_langs, uri_to_iri

import logging
log = logging.getLogger(__name__)


DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
SCHEMA = Namespace('http://schema.org/')
ADMS = Namespace("http://www.w3.org/ns/adms#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
TIME = Namespace('http://www.w3.org/2006/time')
LOCN = Namespace('http://www.w3.org/ns/locn#')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
XML = Namespace('http://www.w3.org/2001/XMLSchema')

SHACL = Namespace("http://www.w3.org/ns/shacl#")

GEOJSON_IMT = 'https://www.iana.org/assignments/media-types/application/vnd.geo+json'  # noqa

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'adms': ADMS,
    'vcard': VCARD,
    'foaf': FOAF,
    'schema': SCHEMA,
    'time': TIME,
    'skos': SKOS,
    'locn': LOCN,
    'gsp': GSP,
    'owl': OWL,
    'xml': XML,
    'sh': SHACL,
}

ogd_theme_base_url = 'http://opendata.swiss/themes'

slug_id_pattern = re.compile('[^/]+(?=/$|$)')


class MultiLangProfile(RDFProfile):
    def _add_multilang_value(self, subject, predicate, dataset_key=None, dataset_dict=None, multilang_values=None):  # noqa
        if not multilang_values and dataset_dict and dataset_key:
            multilang_values = dataset_dict.get(dataset_key)
        if multilang_values:
            try:
                for key, values in multilang_values.iteritems():
                    if values:
                        # the values can be either a multilang-dict or they are
                        # nested in another iterable (e.g. keywords)
                        if not hasattr(values, '__iter__'):
                            values = [values]
                        for value in values:
                            self.g.add((subject, predicate, Literal(value, lang=key)))  # noqa
                    # add default for each language
                    else:
                        self.g.add((subject, predicate, Literal('', lang=key)))  # noqa
            # if multilang_values is not iterable, it is simply added as a non-
            # translated Literal
            except AttributeError:
                self.g.add((subject, predicate, Literal(multilang_values)))

    def _add_multilang_triples_from_dict(self, _dict, subject, items):
        for item in items:
            key, predicate, fallbacks, _type = item
            self._add_multilang_triple_from_dict(
                _dict,
                subject,
                predicate,
                key,
                fallbacks=fallbacks
            )

    def _add_multilang_triple_from_dict(self, _dict, subject, predicate, key, fallbacks=None):  # noqa
        '''
        Adds a new multilang triple to the graph with the provided parameters

        The subject and predicate of the triple are passed as the relevant
        RDFLib objects (URIRef or BNode). The object is always a literal value,
        which is extracted from the dict using the provided key (see
        `_get_dict_value`). If the value for the key is not found, then
        additional fallback keys are checked.
        '''
        value = self._get_dict_value(_dict, key)
        if not value and fallbacks:
            for fallback in fallbacks:
                value = self._get_dict_value(_dict, fallback)
                if value:
                    break

        if value:
            self._add_multilang_value(
                subject,
                predicate,
                multilang_values=value
            )


class SwissDCATAPProfile(MultiLangProfile):
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
        default_lang = 'de'
        lang_dict = {}
        for o in self.g.objects(subject, predicate):
            if multilang and o.language:
                lang_dict[o.language] = unicode(o)
            elif multilang:
                lang_dict[default_lang] = unicode(o)
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
            relation = {
                'label': self._object_value(relation_node, RDFS.label),
                'url': relation_node
            }
            relations.append(relation)

        return relations

    def _keywords(self, subject, predicate):
        keywords = {}
        # initialize the keywords with empty lists for all languages
        for lang in get_langs():
            keywords[lang] = []

        for keyword_node in self.g.objects(subject, predicate):
            lang = keyword_node.language
            keyword = munge_tag(unicode(keyword_node))
            keywords.setdefault(lang, []).append(keyword)

        return keywords

    def _contact_points(self, subject, predicate):

        contact_points = []

        for contact_node in self.g.objects(subject, predicate):
            email = self._object_value(contact_node, VCARD.hasEmail)
            email_clean = email.replace('mailto:', '')
            contact = {
                'name': self._object_value(contact_node, VCARD.fn),
                'email': email_clean
            }

            contact_points.append(contact)

        return contact_points

    def _temporals(self, subject, predicate):

        temporals = []

        for temporal_node in self.g.objects(subject, predicate):
            start_date = self._object_value(temporal_node, SCHEMA.startDate)
            end_date = self._object_value(temporal_node, SCHEMA.endDate)
            if start_date or end_date:
                temporals.append({
                    'start_date': self._clean_datetime(start_date),
                    'end_date': self._clean_datetime(end_date)
                })

        return temporals

    def _clean_datetime(self, datetime_value):
        try:
            d = datetime.strptime(
                datetime_value[0:len('YYYY-MM-DD')],
                '%Y-%m-%d'
            )
            # we have to calculate this manually since the
            # time library of Python 2.7 does not support
            # years < 1900, see OGD-751 and the time docs
            # https://docs.python.org/2.7/library/time.html
            epoch = datetime(1970, 1, 1)
            return int((d - epoch).total_seconds())
        except (ValueError, KeyError, TypeError, IndexError):
            return None

    def parse_dataset(self, dataset_dict, dataset_ref):  # noqa
        log.debug("Parsing dataset '%r'" % dataset_ref)

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
                ('spatial', DCT.spatial),
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
            dataset_dict['tags'].append({'name': munge_tag(unicode(keyword))})

        # Keywords
        dataset_dict['keywords'] = self._keywords(dataset_ref, DCAT.keyword)

        # Themes
        dcat_theme_urls = self._object_value_list(dataset_ref, DCAT.theme)
        if dcat_theme_urls:
            dataset_dict['groups'] = []
            for dcat_theme_url in dcat_theme_urls:
                search_result = slug_id_pattern.search(dcat_theme_url)
                dcat_theme_slug = search_result.group()
                dataset_dict['groups'].append({'name': dcat_theme_slug})

        #  Languages
        languages = self._object_value_list(dataset_ref, DCT.language)
        if languages:
            dataset_dict['language'] = languages

        # Contact details
        dataset_dict['contact_points'] = self._contact_points(
            dataset_ref,
            DCAT.contactPoint
        )

        # Publisher
        dataset_dict['publishers'] = self._publishers(
            dataset_ref,
            DCT.publisher
        )

        # Relations
        dataset_dict['relations'] = self._relations(dataset_ref, DCT.relation)

        # Temporal
        dataset_dict['temporals'] = self._temporals(dataset_ref, DCT.temporal)

        # References
        see_alsos = self._object_value_list(dataset_ref, RDFS.seeAlso)
        for see_also in see_alsos:
            dataset_dict['see_alsos'].append({'dataset_identifier': see_also})

        # Dataset URI (explicitly show the missing ones)
        dataset_uri = (unicode(dataset_ref)
                       if isinstance(dataset_ref, rdflib.term.URIRef)
                       else '')
        dataset_dict['extras'].append({'key': 'uri', 'value': dataset_uri})

        # Resources
        for distribution in self._distributions(dataset_ref):

            resource_dict = {
                'media_type': '',
                'language': [],
            }

            #  Simple values
            for key, predicate in (
                    ('identifier', DCT.identifier),
                    ('format', DCT['format']),
                    ('mimetype', DCAT.mediaType),
                    ('media_type', DCAT.mediaType),
                    ('download_url', DCAT.downloadURL),
                    ('url', DCAT.accessURL),
                    ('rights', DCT.rights),
                    ('license', DCT.license),
                    ):
                value = self._object_value(distribution, predicate)
                if value:
                    resource_dict[key] = value

            # if media type is not set, use format as fallback
            if (not resource_dict.get('media_type') and
                    resource_dict.get('format')):
                resource_dict['media_type'] = resource_dict['format']

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
                                                       DCAT.downloadURL) or '')

            # languages
            for language in self._object_value_list(
                    distribution,
                    DCT.language
            ):
                resource_dict['language'].append(language)

            # byteSize
            byte_size = self._object_value_int(distribution, DCAT.byteSize)
            if byte_size is not None:
                resource_dict['byte_size'] = byte_size

            # Distribution URI (explicitly show the missing ones)
            resource_dict['uri'] = (unicode(distribution)
                                    if isinstance(distribution,
                                                  rdflib.term.URIRef)
                                    else '')

            dataset_dict['resources'].append(resource_dict)

        log.debug("Parsed dataset '%r': %s" % (dataset_ref, dataset_dict))

        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):  # noqa

        log.debug("Create graph from dataset '%s'" % dataset_dict['name'])

        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        g.add((dataset_ref, RDF.type, DCAT.Dataset))

        # Basic fields
        items = [
            ('identifier', DCT.identifier, ['guid', 'id'], Literal),
            ('version', OWL.versionInfo, ['dcat_version'], Literal),
            ('version_notes', ADMS.versionNotes, None, Literal),
            ('frequency', DCT.accrualPeriodicity, None, Literal),
            ('access_rights', DCT.accessRights, None, Literal),
            ('dcat_type', DCT.type, None, Literal),
            ('provenance', DCT.provenance, None, Literal),
            ('spatial', DCT.spatial, None, Literal),
        ]
        self._add_triples_from_dict(dataset_dict, dataset_ref, items)

        self._add_multilang_value(
            dataset_ref,
            DCT.description,
            'description',
            dataset_dict
        )
        self._add_multilang_value(
            dataset_ref,
            DCT.title,
            'title',
            dataset_dict
        )

        # LandingPage
        try:
            landing_page = uri_to_iri(dataset_dict['url'])
        except ValueError:
            landing_page = ''

        g.add((dataset_ref, DCAT.landingPage,
               Literal(landing_page)))

        # Keywords
        self._add_multilang_value(
            dataset_ref,
            DCAT.keyword,
            'keywords',
            dataset_dict
        )

        # Dates
        items = [
            ('issued', DCT.issued, ['metadata_created'], Literal),
            ('modified', DCT.modified, ['metadata_modified'], Literal),
        ]
        self._add_date_triples_from_dict(dataset_dict, dataset_ref, items)

        # Update Interval
        accrual_periodicity = dataset_dict.get('accrual_periodicity')
        if accrual_periodicity:
            g.add((
                dataset_ref,
                DCT.accrualPeriodicity,
                URIRef(accrual_periodicity)
            ))

        # Lists
        items = [
            ('language', DCT.language, None, Literal),
            ('theme', DCAT.theme, None, URIRef),
            ('conforms_to', DCT.conformsTo, None, Literal),
            ('alternate_identifier', ADMS.identifier, None, Literal),
            ('documentation', FOAF.page, None, Literal),
            ('has_version', DCT.hasVersion, None, Literal),
            ('is_version_of', DCT.isVersionOf, None, Literal),
            ('source', DCT.source, None, Literal),
            ('sample', ADMS.sample, None, Literal),
        ]
        self._add_list_triples_from_dict(dataset_dict, dataset_ref, items)

        # Relations
        if dataset_dict.get('relations'):
            relations = dataset_dict.get('relations')
            for relation in relations:
                relation_name = relation['label']
                try:
                    relation_url = uri_to_iri(relation['url'])
                except ValueError:
                    # skip this relation if the URL is invalid
                    continue

                relation = URIRef(relation_url)
                g.add((relation, RDFS.label, Literal(relation_name)))
                g.add((dataset_ref, DCT.relation, relation))

        # References
        if dataset_dict.get('see_alsos'):
            references = dataset_dict.get('see_alsos')
            for reference in references:
                # we only excpect dicts here
                if not isinstance(reference, dict):
                    continue
                reference_identifier = reference.get('dataset_identifier')
                if reference_identifier:
                    g.add((
                        dataset_ref,
                        RDFS.seeAlso,
                        Literal(reference_identifier)
                    ))

        # Contact details
        if dataset_dict.get('contact_points'):
            contact_points = self._get_dataset_value(dataset_dict, 'contact_points')  # noqa
            for contact_point in contact_points:
                contact_details = BNode()
                contact_point_email = contact_point['email']
                contact_point_name = contact_point['name']

                g.add((contact_details, RDF.type, VCARD.Organization))
                g.add((contact_details, VCARD.hasEmail, URIRef(contact_point_email)))  # noqa
                g.add((contact_details, VCARD.fn, Literal(contact_point_name)))

                g.add((dataset_ref, DCAT.contactPoint, contact_details))

        # Publisher
        if dataset_dict.get('publishers'):
            publishers = dataset_dict.get('publishers')
            for publisher in publishers:
                publisher_name = publisher['label']

                publisher_details = BNode()
                g.add((publisher_details, RDF.type, RDF.Description))
                g.add((publisher_details, RDFS.label, Literal(publisher_name)))
                g.add((dataset_ref, DCT.publisher, publisher_details))

        # Temporals
        temporals = dataset_dict.get('temporals')
        if temporals:
            for temporal in temporals:
                start = temporal['start_date']
                end = temporal['end_date']
                if start or end:
                    temporal_extent = BNode()
                    g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
                    if start:
                        self._add_date_triple(
                            temporal_extent,
                            SCHEMA.startDate,
                            start
                        )
                    if end:
                        self._add_date_triple(
                            temporal_extent,
                            SCHEMA.endDate,
                            end
                        )
                    g.add((dataset_ref, DCT.temporal, temporal_extent))

        # Themes
        groups = self._get_dataset_value(dataset_dict, 'groups')
        for group_name in groups:
            g.add((
                dataset_ref,
                DCAT.theme,
                URIRef('%s/%s' % (ogd_theme_base_url, group_name.get('name')))
            ))

        # Resources
        for resource_dict in dataset_dict.get('resources', []):

            distribution = URIRef(resource_uri(resource_dict))

            g.add((dataset_ref, DCAT.distribution, distribution))
            g.add((distribution, RDF.type, DCAT.Distribution))

            #  Simple values
            items = [
                ('status', ADMS.status, None, Literal),
                ('rights', DCT.rights, None, Literal),
                ('license', DCT.license, None, Literal),
                ('identifier', DCT.identifier, None, Literal),
                ('media_type', DCAT.mediaType, None, Literal),
                ('spatial', DCT.spatial, None, Literal),
            ]

            self._add_triples_from_dict(resource_dict, distribution, items)

            self._add_multilang_value(distribution, DCT.title, 'display_name', resource_dict)  # noqa
            self._add_multilang_value(distribution, DCT.description, 'description', resource_dict)  # noqa

            #  Lists
            items = [
                ('documentation', FOAF.page, None, Literal),
                ('language', DCT.language, None, Literal),
                ('conforms_to', DCT.conformsTo, None, Literal),
            ]
            self._add_list_triples_from_dict(resource_dict, distribution,
                                             items)

            # Download URL & Access URL
            download_url = resource_dict.get('download_url')
            if download_url:
                try:
                    download_url = uri_to_iri(download_url)
                    g.add((
                        distribution,
                        DCAT.downloadURL,
                        URIRef(download_url)
                    ))
                except ValueError:
                    # only add valid URL
                    pass

            url = resource_dict.get('url')
            if (url and not download_url) or (url and url != download_url):
                try:
                    url = uri_to_iri(url)
                    g.add((distribution, DCAT.accessURL, URIRef(url)))
                except ValueError:
                    # only add valid URL
                    pass
            elif download_url:
                g.add((distribution, DCAT.accessURL, URIRef(download_url)))

            # Format
            if resource_dict.get('format'):
                g.add((
                    distribution,
                    DCT['format'],
                    Literal(resource_dict['format'])
                ))

            # Mime-Type
            if resource_dict.get('mimetype'):
                g.add((
                    distribution,
                    DCAT.mediaType,
                    Literal(resource_dict['mimetype'])
                ))

            # Dates
            items = [
                ('issued', DCT.issued, None, Literal),
                ('modified', DCT.modified, None, Literal),
            ]

            self._add_date_triples_from_dict(resource_dict, distribution,
                                             items)

            # ByteSize
            if resource_dict.get('byte_size'):
                g.add((distribution, DCAT.byteSize,
                       Literal(resource_dict['byte_size'])))

    def graph_from_catalog(self, catalog_dict, catalog_ref):
        g = self.g
        g.add((catalog_ref, RDF.type, DCAT.Catalog))


class SwissSchemaOrgProfile(SchemaOrgProfile, MultiLangProfile):
    def _basic_fields_graph(self, dataset_ref, dataset_dict):
        items = [
            ('identifier', SCHEMA.identifier, None, Literal),
            ('version', SCHEMA.version, ['dcat_version'], Literal),
            ('issued', SCHEMA.datePublished, ['metadata_created'], Literal),
            ('modified', SCHEMA.dateModified, ['metadata_modified'], Literal),
            ('author', SCHEMA.author, ['contact_name', 'maintainer'], Literal),
            ('url', SCHEMA.sameAs, None, Literal),
        ]
        self._add_triples_from_dict(dataset_dict, dataset_ref, items)

        items = [
            ('title', SCHEMA.name, None, Literal),
            ('description', SCHEMA.description, None, Literal),
        ]
        self._add_multilang_triples_from_dict(dataset_dict, dataset_ref, items)

    def _list_fields_graph(self, dataset_ref, dataset_dict):
        items = [
            ('language', SCHEMA.inLanguage, None, Literal),
        ]
        self._add_list_triples_from_dict(dataset_dict, dataset_ref, items)

    def _publisher_graph(self, dataset_ref, dataset_dict):
        if any([
            self._get_dataset_value(dataset_dict, 'publisher_uri'),
            self._get_dataset_value(dataset_dict, 'publisher_name'),
            dataset_dict.get('organization'),
        ]):

            publisher_uri = publisher_uri_from_dataset_dict(dataset_dict)
            if publisher_uri:
                publisher_details = URIRef(publisher_uri)
            else:
                # No organization nor publisher_uri
                publisher_details = BNode()

            self.g.add((publisher_details, RDF.type, SCHEMA.Organization))
            self.g.add((dataset_ref, SCHEMA.publisher, publisher_details))
            self.g.add((dataset_ref, SCHEMA.sourceOrganization, publisher_details))  # noqa

            publisher_name = self._get_dataset_value(
                dataset_dict,
                'publisher_name'
            )
            if not publisher_name and dataset_dict.get('organization'):
                publisher_name = dataset_dict['organization']['title']
                self._add_multilang_value(
                    publisher_details,
                    SCHEMA.name,
                    multilang_values=publisher_name
                )
            else:
                g.add((publisher_details, SCHEMA.name, Literal(publisher_name)))  # noqa

            contact_point = BNode()
            self.g.add((publisher_details, SCHEMA.contactPoint, contact_point))

            self.g.add((contact_point, SCHEMA.contactType, Literal('customer service')))  # noqa

            publisher_url = self._get_dataset_value(dataset_dict, 'publisher_url')  # noqa
            if not publisher_url and dataset_dict.get('organization'):
                publisher_url = dataset_dict['organization'].get('url') or config.get('ckan.site_url', '')  # noqa

            self.g.add((contact_point, SCHEMA.url, Literal(publisher_url)))
            items = [
                ('publisher_email', SCHEMA.email, ['contact_email', 'maintainer_email', 'author_email'], Literal),  # noqa
                ('publisher_name', SCHEMA.name, ['contact_name', 'maintainer', 'author'], Literal),  # noqa
            ]

            self._add_triples_from_dict(dataset_dict, contact_point, items)

    def _temporal_graph(self, dataset_ref, dataset_dict):
        # schema.org temporalCoverage only allows to specify one temporal
        # DCAT-AP Switzerland allows to specify multiple
        # for the mapping we always use the first one
        temporals = self._get_dataset_value(dataset_dict, 'temporals')
        try:
            start = temporals[0].get('start_date')
            end = temporals[0].get('end_date')
        except (IndexError, KeyError, TypeError):
            # do not add temporals if there are none
            return
        if start or end:
            if start and end:
                self.g.add((dataset_ref, SCHEMA.temporalCoverage, Literal('%s/%s' % (start, end))))  # noqa
            elif start:
                self._add_date_triple(dataset_ref, SCHEMA.temporalCoverage, start)  # noqa
            elif end:
                self._add_date_triple(dataset_ref, SCHEMA.temporalCoverage, end)  # noqa

    def _tags_graph(self, dataset_ref, dataset_dict):
        for tag in dataset_dict.get('keywords', []):
            items = [
                ('keywords', SCHEMA.keywords, None, Literal),
            ]
            self._add_multilang_triples_from_dict(
                dataset_dict,
                dataset_ref,
                items
            )

    def _distribution_basic_fields_graph(self, distribution, resource_dict):
        items = [
            ('issued', SCHEMA.datePublished, None, Literal),
            ('modified', SCHEMA.dateModified, None, Literal),
        ]

        self._add_triples_from_dict(resource_dict, distribution, items)

        items = [
            ('title', SCHEMA.name, None, Literal),
            ('description', SCHEMA.description, None, Literal),
        ]
        self._add_multilang_triples_from_dict(
            resource_dict,
            distribution,
            items
        )


class SHACLResultProfile(object):

    def __init__(self, graph):
        self.r = graph

    def shaclresults_grouped_by_node(self):
        """parsing the shacl results"""
        error_dict_grouped_by_node = defaultdict(list)
        ref_processed_count = 0
        for result_ref in self.r.subjects(RDF.type, SHACL.ValidationResult):
            result_dict = self._shaclresult(result_ref)
            focusnode = self.r.value(result_ref, SHACL.focusNode)
            if isinstance(focusnode, URIRef):
                node = unicode(focusnode)
            else:
                node = ('catalog')
            try:
                value = ""
                if 'value' in result_dict:
                    value = ", Value: [{}]".format(
                        result_dict['value'].encode('utf-8'))
                message = """[{}]: {}: [{}]: '{}' {} ({})""".format(
                        node.encode('utf-8'),
                        result_dict.get('severity', ''),
                        result_dict.get('path', ''),
                        result_dict.get('message', '').encode('utf-8'),
                        value,
                        result_dict.get('constraint', '').encode('utf-8'))
            except UnicodeEncodeError as e:
                log.error("SHACL error for parsing results"
                          .format(e))
                raise
            else:
                error_dict_grouped_by_node[node].append(message)
            ref_processed_count += 1
        log.debug("SHACL: {} number of shacl results processed and grouped"
                  .format(ref_processed_count))
        return error_dict_grouped_by_node

    def _shaclresult(self, result_ref):
        """parsing a shacl result"""
        result_dict = {}
        for key, predicate in (
                ('message', SHACL.resultMessage),
                ('value', SHACL.value),
                ('path', SHACL.resultPath),
                ('detail', SHACL.resultDetail),
                ('severity', SHACL.resultSeverity),
                ('constraint', SHACL.sourceConstraintComponent),
        ):
            value = self._object_value(result_ref, predicate)
            if value:
                result_dict[key] = value
        return result_dict

    def _object_value(self, subject, predicate):
        """get the value of an object using the namespace"""
        o = self.r.value(subject, predicate)
        if isinstance(o, rdflib.Literal):
            return unicode(o)
        elif isinstance(o, rdflib.URIRef):
            return self.r.namespace_manager.qname(o)
        else:
            return None
