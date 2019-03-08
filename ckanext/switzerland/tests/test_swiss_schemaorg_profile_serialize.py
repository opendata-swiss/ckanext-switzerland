import json

import nose

from rdflib import URIRef, BNode, Literal
from rdflib.namespace import RDF

from ckanext.dcat import utils
from ckanext.dcat.processors import RDFSerializer
from ckanext.dcat.profiles import SCHEMA

from ckanext.dcat.tests.test_euro_dcatap_profile_serialize import BaseSerializeTest

eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true


class TestSchemaOrgProfileSerializeDataset(BaseSerializeTest):

    def test_graph_from_dataset(self):

        dataset = {
            'id': '4b6fe9ca-dc77-4cec-92a4-55c6624a5bd6',
            'name': 'test-dataset',
            'title': 'Test DCAT dataset',
            'url': 'http://example.com/ds1',
            'version': '1.0b',
            'metadata_created': '2015-06-26T15:21:09.034694',
            'metadata_modified': '2015-06-26T15:21:09.075774',
            'keywords':
                {
                    'fr': [],
                    'de': [
                        'alter',
                        'sozialhilfe'
                    ],
                    'en': [
                        'age'
                    ],
                    'it': []
                },
            'groups': [
                {
                    'display_name':
                        {
                            'fr': 'Economie nationale',
                            'de': 'Volkswirtschaft',
                            'en': 'National economy',
                            'it': 'Economia'
                        },
                    'description':
                        {
                            'fr': '',
                            'de': '',
                            'en': '',
                            'it': ''
                        },
                    'image_display_url': '',
                    'title':
                        {
                            'fr': 'Economie nationale',
                            'de': 'Volkswirtschaft',
                            'en': 'National economy',
                            'it': 'Economia'
                        },
                    'id': '5389c3f2-2f64-436b-9fac-2d1fc342f7b5',
                    'name': 'national-economy'
                },
                {
                    'display_name':
                        {
                            'fr': 'Education, science',
                            'de': 'Bildung, Wissenschaft',
                            'en': 'Education and science',
                            'it': 'Formazione e scienza'
                        },
                    'description':
                        {
                            'fr': '',
                            'de': '',
                            'en': '',
                            'it': ''
                        },
                    'image_display_url': '',
                    'title':
                        {
                            'fr': 'Education, science',
                            'de': 'Bildung, Wissenschaft',
                            'en': 'Education and science',
                            'it': 'Formazione e scienza'
                        },
                    'id': 'afcb4a2a-b4b0-4d7c-984a-9078e964be49',
                    'name': 'education'
                },
                {
                    'display_name':
                        {
                            'fr': 'Finances',
                            'de': 'Finanzen',
                            'en': 'Finances',
                            'it': 'Finanze'
                        },
                    'description':
                        {
                            'fr': '',
                            'de': '',
                            'en': '',
                            'it': ''
                        },
                    'image_display_url': '',
                    'title':
                        {
                            'fr': 'Finances',
                            'de': 'Finanzen',
                            'en': 'Finances',
                            'it': 'Finanze'
                        },
                    'id': '79cbe120-e9c6-4249-b934-58ca980606d7',
                    'name': 'finances'
                }
            ],
            'description': {
                'fr': '',
                'de': 'Deutsche Beschreibung',
                'en': 'English Description',
                'it': ''
            },
            'extras': [
                {'key': 'alternate_identifier', 'value': '[\"xyz\", \"abc\"]'},
                {'key': 'identifier', 'value': '26be5452-fc5c-11e7-8450-fea9aa178066'},
                {'key': 'version_notes', 'value': 'This is a beta version'},
                {'key': 'frequency', 'value': 'monthly'},
                {'key': 'language', 'value': '[\"en\"]'},
                {'key': 'theme', 'value': '[\"http://eurovoc.europa.eu/100142\", \"http://eurovoc.europa.eu/100152\"]'},
                {'key': 'conforms_to', 'value': '[\"Standard 1\", \"Standard 2\"]'},
                {'key': 'access_rights', 'value': 'public'},
                {'key': 'documentation', 'value': '[\"http://dataset.info.org/doc1\", \"http://dataset.info.org/doc2\"]'},
                {'key': 'provenance', 'value': 'Some statement about provenance'},
                {'key': 'dcat_type', 'value': 'test-type'},
                {'key': 'related_resource', 'value': '[\"http://dataset.info.org/related1\", \"http://dataset.info.org/related2\"]'},
                {'key': 'has_version', 'value': '[\"https://data.some.org/catalog/datasets/derived-dataset-1\", \"https://data.some.org/catalog/datasets/derived-dataset-2\"]'},
                {'key': 'is_version_of', 'value': '[\"https://data.some.org/catalog/datasets/original-dataset\"]'},
                {'key': 'source', 'value': '[\"https://data.some.org/catalog/datasets/source-dataset-1\", \"https://data.some.org/catalog/datasets/source-dataset-2\"]'},
                {'key': 'sample', 'value': '[\"https://data.some.org/catalog/datasets/9df8df51-63db-37a8-e044-0003ba9b0d98/sample\"]'},
            ]
        }
        extras = self._extras(dataset)

        s = RDFSerializer(profiles=['swiss_schemaorg'])
        g = s.g

        dataset_ref = s.graph_from_dataset(dataset)

        eq_(unicode(dataset_ref), utils.dataset_uri(dataset))

        # Basic fields
        assert self._triple(g, dataset_ref, RDF.type, SCHEMA.Dataset)
        assert self._triple(g, dataset_ref, SCHEMA.name, dataset['title'])
        assert self._triple(g, dataset_ref, SCHEMA.version, dataset['version'])
        assert self._triple(g, dataset_ref, SCHEMA.identifier, extras['identifier'])

        # Dates
        assert self._triple(g, dataset_ref, SCHEMA.datePublished, dataset['metadata_created'])
        assert self._triple(g, dataset_ref, SCHEMA.dateModified, dataset['metadata_modified'])

        for key, value in dataset['description'].iteritems():
            assert self._triple(g, dataset_ref, SCHEMA.description, Literal(value, lang=key))
        eq_(len([t for t in g.triples((dataset_ref, SCHEMA.description, None))]), 4)

        # Tags
        eq_(len([t for t in g.triples((dataset_ref, SCHEMA.keywords, None))]), 5)
        for key, keywords in dataset['keywords'].iteritems():
            for keyword in keywords:
                assert self._triple(g, dataset_ref, SCHEMA.keywords, Literal(keyword, lang=key))

        # List
        for item in [
            ('language', SCHEMA.inLanguage, Literal),
        ]:
            values = json.loads(extras[item[0]])
            eq_(len([t for t in g.triples((dataset_ref, item[1], None))]), len(values))
            for value in values:
                assert self._triple(g, dataset_ref, item[1], item[2](value))