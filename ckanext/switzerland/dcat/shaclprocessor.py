import csv
import logging
import xml
import os

import rdflib
from rdflib.namespace import RDF, NamespaceManager, Namespace

from ckanext.dcat.processors import RDFParserException

SHACL = Namespace("http://www.w3.org/ns/shacl#")

log = logging.getLogger(__name__)


class SHACLParserException(RDFParserException):
    pass


class ShaclParser(object):

    def __init__(self, resultpath, harvest_source_id, page_count):
        self.harvest_source_id = harvest_source_id
        self.page_count = page_count
        self.csvfile = self._get_csv_path(resultpath)
        self.g = rdflib.Graph()
        try:
            self.g.parse(resultpath, format='turtle')
        except (SyntaxError, xml.sax.SAXParseException,
                rdflib.plugin.PluginException, TypeError), e:
            raise SHACLParserException(e)
        log.debug(
            "SHACL result graph parsed: length: {}"
            .format(len(self.g)))
        self.g.bind('sh', SHACL)
        self.g.namespace_manager = NamespaceManager(self.g)
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
        self.shaclerrors = []

    def parse(self):
        """parsing the shacl results"""
        for result_ref in self.g.subjects(RDF.type, SHACL.ValidationResult):
            result_dict = self._shaclresult(result_ref)
            self.shaclerrors.append(result_dict)
        self.shaclerrors.sort()
        log.debug("SHACL: {} number of shacl results processed"
                  .format(len(self.shaclerrors)))

    def _shaclresult(self, result_ref):
        """parsing a shacl result"""
        result_dict = {}
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
            elif isinstance(o, rdflib.URIRef) and predicate == SHACL.focusNode:
                return unicode(o)
            elif isinstance(o, rdflib.BNode) and predicate == SHACL.focusNode:
                return 'catalog'
            elif isinstance(o, rdflib.URIRef):
                return self._decode_urirefs(o)
            else:
                return None
        except Exception as e:
            return "ShaclResultParseError: {}".format(e)

    def _get_csv_path(self, resultpath):
        path, filename = os.path.split(resultpath)
        return os.path.join(
            path, filename.replace('ttl', 'csv'))

    def _make_string_safe(self, value):
        try:
            return value.encode('utf-8')
        except Exception as e:
            return "ShaclResultParseError: {}".format(e)

    def _decode_urirefs(self, o):
        try:
            return self.g.namespace_manager.qname(o)
        except Exception as e:
            try:
                return str(o)
            except Exception as e:
                return "ShaclResultParseError: {}".format(e)

    def write_csv_file(self):
        csv_headers = ['harvest_source_id', 'page_count']
        csv_headers.extend(self.shaclkeys)
        with open(self.csvfile, 'w') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=csv_headers,
                delimiter='|', restval='')
            writer.writeheader()
            for error_dict in self.shaclerrors:
                error_dict['harvest_source_id'] = self.harvest_source_id
                error_dict['page_count'] = self.page_count
                writer.writerow(error_dict)

    def _get_error_message(self, result_dict):
        message = "[{}] : ".format(result_dict['sh_focusnode'])
        for key in self.shaclkeys[1:]:
            value = result_dict.get(key, '')
            if value:
                message += "({}): {}; ".format(key, value)
        return message

    def shacl_error_messages(self):
        for error_dict in self.shaclerrors:
            yield self._get_error_message(error_dict)
