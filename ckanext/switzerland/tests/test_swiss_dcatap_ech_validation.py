from datetime import datetime

import nose
import rdflib

try:
    from ckan.tests import helpers
except ImportError:
    from ckan.new_tests import helpers

from ckanext.switzerland.dcat.profiles import (SHACL, SHACLResultProfile)


eq_ = nose.tools.eq_
assert_true = nose.tools.assert_true

class BaseParseTest(object):
    def test_parse_shacl_data(self):
        data = '''
@prefix schema: <http://schema.org/> .
@prefix dct:   <http://purl.org/dc/terms/> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix odrs:  <http://schema.theodi.org/odrs#> .
@prefix xml:   <http://www.w3.org/XML/1998/namespace> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix dcat:  <http://www.w3.org/ns/dcat#> .
@prefix foaf:  <http://xmlns.com/foaf/0.1/> .
@prefix dc:    <http://purl.org/dc/elements/1.1/> .

[ a       <http://www.w3.org/ns/shacl#ValidationReport> ;
  <http://www.w3.org/ns/shacl#conforms>
          false ;
  <http://www.w3.org/ns/shacl#result>
          [ a       <http://www.w3.org/ns/shacl#ValidationResult> ;
            <http://www.w3.org/ns/shacl#focusNode>
                    <https://data.bs.ch/api/v2/catalog/datasets/100004> ;
            <http://www.w3.org/ns/shacl#resultMessage>
                    "Value must be an instance of foaf:Document" ;
            <http://www.w3.org/ns/shacl#resultPath>
                    dcat:landingPage ;
            <http://www.w3.org/ns/shacl#resultSeverity>
                    <http://www.w3.org/ns/shacl#Violation> ;
            <http://www.w3.org/ns/shacl#sourceConstraintComponent>
                    <http://www.w3.org/ns/shacl#ClassConstraintComponent> ;
            <http://www.w3.org/ns/shacl#sourceShape>
                    _:b0 ;
            <http://www.w3.org/ns/shacl#value>
                    "https://data.bs.ch/explore/dataset/100004/"
          ] ;
  <http://www.w3.org/ns/shacl#result>
          [ a       <http://www.w3.org/ns/shacl#ValidationResult> ;
            <http://www.w3.org/ns/shacl#focusNode>
                    <https://data.bs.ch/api/v2/catalog/datasets/100004/exports/json> ;
            <http://www.w3.org/ns/shacl#resultMessage>
                    "Value must be an instance of dct:MediaTypeOrExtent" ;
            <http://www.w3.org/ns/shacl#resultPath>
                    dct:format ;
            <http://www.w3.org/ns/shacl#resultSeverity>
                    <http://www.w3.org/ns/shacl#Violation> ;
            <http://www.w3.org/ns/shacl#sourceConstraintComponent>
                    <http://www.w3.org/ns/shacl#ClassConstraintComponent> ;
            <http://www.w3.org/ns/shacl#sourceShape>
                    _:b1 ;
            <http://www.w3.org/ns/shacl#value>
                    "json"
          ] ;
        '''
        r = rdflib.Graph()
        r.parse(data, format='n3')
        r.bind('sh', SHACL)
        r.namespace_manager = rdflib.NamespaceManager(r)

        p = SHACLResultProfile(r)
        assert(len(p.shaclresults())) == 2

        eq_(len(p.r), 0)


        eq_(len(p.r), 2)
