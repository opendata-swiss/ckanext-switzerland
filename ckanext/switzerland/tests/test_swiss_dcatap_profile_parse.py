# -*- coding: utf-8 -*-

import os
from datetime import datetime

import nose

from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF

try:
    from ckan.tests import helpers
except ImportError:
    from ckan.new_tests import helpers

from ckanext.dcat.processors import RDFParser
from ckanext.switzerland.dcat.profiles import (DCAT, DCT)

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class BaseParseTest(object):

    def _extras(self, dataset):
        extras = {}
        for extra in dataset.get('extras'):
            extras[extra['key']] = extra['value']
        return extras

    def _get_file_contents(self, file_name):
        path = os.path.join(os.path.dirname(__file__),
                            'fixtures',
                            file_name)
        with open(path, 'r') as f:
            return f.read()


class TestSwissDCATAPProfileParsing(BaseParseTest):

    def test_dataset_all_fields(self):

        contents = self._get_file_contents('1901.xml')

        p = RDFParser(profiles=['swiss_dcat_ap'])

        p.parse(contents)

        datasets = [d for d in p.datasets()]

        eq_(len(datasets), 1)

        dataset = datasets[0]
        extras = self._extras(dataset)

        # Basic fields
        assert all(l in dataset['title'] for l in ['de', 'fr', 'it', 'en']), "title contains all languages"
        eq_(dataset['title']['de'], u'Statistisches Jahrbuch der Schweiz 1901')
        eq_(dataset['title']['fr'], u'Annuaire statistique de la Suisse 1901')

        assert all(l in dataset['description'] for l in ['de', 'fr', 'it', 'en']), "description contains all languages"
        eq_(dataset['description']['de'], u'')
        eq_(dataset['url'], u'https://www.bfs.admin.ch/bfs/de/home/statistiken.html')

        # Keywords
        assert all(l in dataset['keywords'] for l in ['de', 'fr', 'it', 'en']), "keywords contains all languages"
        eq_(sorted(dataset['keywords']['de']), ['publikation', 'statistische-grundlagen-und-ubersichten'])
        eq_(sorted(dataset['keywords']['fr']), ['bases-statistiques-et-generalites', 'publication'])
        eq_(sorted(dataset['keywords']['it']), ['basi-statistiche-e-presentazioni-generali', 'pubblicazione'])
        eq_(sorted(dataset['keywords']['en']), ['publication', 'statistical-basis-and-overviews'])
        eq_(sorted(dataset['tags'], key=lambda k: k['name']), [{'name': 'basas-statisticas-e-survistas'},
                                                               {'name': 'bases-statistiques-et-generalites'},
                                                               {'name': 'basi-statistiche-e-presentazioni-generali'},
                                                               {'name': 'pubblicazione'},
                                                               {'name': 'publication'},
                                                               {'name': 'publication'},
                                                               {'name': 'publikation'},
                                                               {'name': 'statistical-basis-and-overviews'},
                                                               {'name': 'statistische-grundlagen-und-ubersichten'}])

        #  Simple values
        eq_(dataset['issued'], -2177539200)
        eq_(dataset['modified'], 1524528000)
        eq_(dataset['identifier'], u'346266@bundesamt-fur-statistik-bfs')
        eq_(dataset['spatial'], 'Schweiz')

        # Temporals
        temporal = dataset['temporals'][0]
        eq_(temporal['end_date'], -2146003200)
        end_date = datetime.fromtimestamp(temporal['end_date'])
        eq_(end_date.date().isoformat(), '1901-12-31')

        eq_(temporal['start_date'], -2177452800)
        start_date = datetime.fromtimestamp(temporal['start_date'])
        eq_(start_date.date().isoformat(), '1901-01-01')

        # Publisher
        publisher = dataset['publishers'][0]
        eq_(publisher['label'], 'BFS/OFS')

        # Contact points
        contact_point = dataset['contact_points'][0]
        eq_(contact_point['name'], 'info@bfs.admin.ch')
        eq_(contact_point['email'], 'auskunftsdienst@bfs.admin.ch')

        # See alsos
        see_also = dataset['see_alsos'][0]
        eq_(see_also['dataset_identifier'], u'4682791@bundesamt-fur-statistik-bfs')

        #  Lists
        eq_(sorted(dataset['language']), [u'de', u'fr'])
        eq_(sorted(dataset['groups']), [{'name': u'statistical-basis'}])

        # Dataset URI
        eq_(extras['uri'], u'https://opendata.swiss/dataset/7451e012-64b2-4bbc-af20-a0e2bc61b585')

        # Resources
        eq_(len(dataset['resources']), 1)
        resource = dataset['resources'][0]

        #  Simple values
        assert all(l in resource['title'] for l in ['de', 'fr', 'it', 'en']), "resource title contains all languages"
        eq_(resource['title']['fr'], u'Annuaire statistique de la Suisse 1901')
        eq_(resource['title']['de'], u'')
        assert all(l in resource['description'] for l in ['de', 'fr', 'it', 'en']), "resource description contains all languages"
        eq_(resource['description']['de'], u'')
        eq_(resource['format'], u'HTML')
        eq_(resource['mimetype'], u'text/html')
        eq_(resource['media_type'], u'text/html')
        eq_(resource['identifier'], u'346265-fr@bundesamt-fur-statistik-bfs')
        eq_(resource['rights'], u'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired')
        eq_(resource['language'], [u'fr'])
        eq_(resource['issued'], -2177539200)
        eq_(resource['url'], u'https://www.bfs.admin.ch/asset/fr/hs-b-00.01-jb-1901')
        assert 'download_url' not in resource, "download_url not available on resource"

        # Distribution URI
        eq_(resource['uri'], u'https://opendata.swiss/dataset/7451e012-64b2-4bbc-af20-a0e2bc61b585/resource/c8ec6ca0-6923-4cf3-92f2-95a10e6f8e25')

    def test_dataset_issued_with_year_before_1900(self):

        contents = self._get_file_contents('1894.xml')

        p = RDFParser(profiles=['swiss_dcat_ap'])

        p.parse(contents)

        datasets = [d for d in p.datasets()]

        eq_(len(datasets), 1)

        dataset = datasets[0]

        # Check date values
        eq_(dataset['issued'], -2398377600)
        issued = datetime.fromtimestamp(dataset['issued'])
        eq_(issued.date().isoformat(), u'1893-12-31')

        eq_(dataset['modified'], 1524528000)
        modified = datetime.fromtimestamp(dataset['modified'])
        eq_(modified.date().isoformat(), u'2018-04-24')

    def test_catalog(self):

        contents = self._get_file_contents('catalog.xml')

        p = RDFParser(profiles=['swiss_dcat_ap'])

        p.parse(contents)

        datasets = [d for d in p.datasets()]

        eq_(len(datasets), 2)

    def test_distribution_access_url(self):
        g = Graph()

        dataset1 = URIRef("http://example.org/datasets/1")
        g.add((dataset1, RDF.type, DCAT.Dataset))

        distribution1_1 = URIRef("http://example.org/datasets/1/ds/1")
        g.add((distribution1_1, RDF.type, DCAT.Distribution))
        g.add((distribution1_1, DCAT.accessURL, Literal('http://access.url.org')))
        g.add((dataset1, DCAT.distribution, distribution1_1))

        p = RDFParser(profiles=['swiss_dcat_ap'])

        p.g = g

        datasets = [d for d in p.datasets()]

        resource = datasets[0]['resources'][0]

        eq_(resource['url'], u'http://access.url.org')
        assert 'download_url' not in resource

    def test_distribution_download_url(self):
        g = Graph()

        dataset1 = URIRef("http://example.org/datasets/1")
        g.add((dataset1, RDF.type, DCAT.Dataset))

        distribution1_1 = URIRef("http://example.org/datasets/1/ds/1")
        g.add((distribution1_1, RDF.type, DCAT.Distribution))
        g.add((distribution1_1, DCAT.downloadURL, Literal('http://download.url.org')))
        g.add((dataset1, DCAT.distribution, distribution1_1))

        p = RDFParser(profiles=['swiss_dcat_ap'])

        p.g = g

        datasets = [d for d in p.datasets()]

        resource = datasets[0]['resources'][0]

        eq_(resource['url'], u'http://download.url.org')
        eq_(resource['download_url'], u'http://download.url.org')

    def test_distribution_both_access_and_download_url(self):
        g = Graph()

        dataset1 = URIRef("http://example.org/datasets/1")
        g.add((dataset1, RDF.type, DCAT.Dataset))

        distribution1_1 = URIRef("http://example.org/datasets/1/ds/1")
        g.add((distribution1_1, RDF.type, DCAT.Distribution))
        g.add((distribution1_1, DCAT.accessURL, Literal('http://access.url.org')))
        g.add((distribution1_1, DCAT.downloadURL, Literal('http://download.url.org')))
        g.add((dataset1, DCAT.distribution, distribution1_1))

        p = RDFParser(profiles=['swiss_dcat_ap'])

        p.g = g

        datasets = [d for d in p.datasets()]

        resource = datasets[0]['resources'][0]

        eq_(resource['url'], u'http://access.url.org')
        eq_(resource['download_url'], u'http://download.url.org')

    def test_distribution_format_format_only(self):
        g = Graph()

        dataset1 = URIRef("http://example.org/datasets/1")
        g.add((dataset1, RDF.type, DCAT.Dataset))

        distribution1_1 = URIRef("http://example.org/datasets/1/ds/1")
        g.add((distribution1_1, RDF.type, DCAT.Distribution))
        g.add((distribution1_1, DCT['format'], Literal('CSV')))
        g.add((dataset1, DCAT.distribution, distribution1_1))

        p = RDFParser(profiles=['swiss_dcat_ap'])

        p.g = g

        datasets = [d for d in p.datasets()]

        resource = datasets[0]['resources'][0]

        eq_(resource['format'], u'CSV')
