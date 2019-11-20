import logging
import xml

import rdflib
from rdflib.namespace import RDF, NamespaceManager, Namespace, SKOS

from ckanext.dcat.processors import RDFParserException

SHACL = Namespace("http://www.w3.org/ns/shacl#")
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


log = logging.getLogger(__name__)


class SHACLParserException(RDFParserException):
    pass


class ShaclParser(object):

    def __init__(self, resultpath, harvest_source_id):
        self.path = resultpath
        self.g = rdflib.Graph()
        for k, v in namespaces.items():
            self.g.bind(k, v)
        self.g.namespace_manager = NamespaceManager(self.g)
        self.harvest_source_id = harvest_source_id
        self.shaclkeys = ['sh_focusnode',
                          'sh_severity',
                          'sh_path',
                          'sh_constraint',
                          'sh_message',
                          'sh_value',
                          'sh_shape',
                          'sh_detail']
        self.shaclpredicates = [SHACL.focusNode,
                                SHACL.resultSeverity,
                                SHACL.resultPath,
                                SHACL.sourceConstraintComponent,
                                SHACL.resultMessage,
                                SHACL.value,
                                SHACL.sourceShape,
                                SHACL.resultDetail]

        self.resultdictkeys = self.shaclkeys[:]
        self.resultdictkey_parseerror = 'parseerror'
        self.resultdictkey_harvestsourceid = 'harvest_source_id'
        self.resultdictkeys.extend(
            [self.resultdictkey_harvestsourceid,
             self.resultdictkey_parseerror])

    def parse(self):
        try:
            self.g.parse(self.path, format='turtle')
        except (SyntaxError, xml.sax.SAXParseException,
                rdflib.plugin.PluginException, TypeError), e:
            raise SHACLParserException(e)

    def shaclresults(self):
        """parsing the shacl results"""
        for result_ref in self.g.subjects(RDF.type, SHACL.ValidationResult):
            result_dict = {
                self.resultdictkey_harvestsourceid: self.harvest_source_id
            }
            try:
                result_dict = self._shaclresult(result_ref)
            except SHACLParserException as e:
                result_dict[self.resultdictkey_parseerror] = e
            finally:
                yield result_dict

    def _shaclresult(self, result_ref):
        """parsing a shacl result"""
        result_dict = {
            self.resultdictkey_harvestsourceid: self.harvest_source_id}
        for key, predicate in zip(self.shaclkeys, self.shaclpredicates):
            value = self._object_value(result_ref, predicate)
            if predicate in [
                'sh_message', 'sh_value',
                'sh_constraint', 'sh_shape'
            ]:
                value = self._make_string_safe(value)
            if value:
                result_dict[key] = value
        return result_dict

    def _object_value(self, subject, predicate):
        """get the value of an object using the namespace"""
        o = self.g.value(subject, predicate)
        try:
            if isinstance(o, rdflib.Literal):
                return unicode(o)
            elif isinstance(o, rdflib.BNode):
                return o
            elif isinstance(o, rdflib.URIRef):
                return self._decode_urirefs(o)
            else:
                return None
        except Exception as e:
            raise SHACLParserException(
                "exception occured getting object value for {} {}: {}"
                .format(subject, predicate, e))

    def _make_string_safe(self, value):
        try:
            return value.encode('utf-8')
        except Exception as e:
            raise SHACLParserException(
                "exception occured while encoding utf-8 for {}: {}"
                .format(value, e))

    def _decode_urirefs(self, o):
        try:
            return self.g.namespace_manager.qname(o)
        except Exception as e:
            try:
                return str(o)
            except Exception as e:
                raise SHACLParserException(
                    "exception occured decoding uriref for {}: {}"
                    .format(o, e))
