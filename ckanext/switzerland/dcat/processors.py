from __future__ import print_function

import os
import xml
import logging
import subprocess

import rdflib
import rdflib.parser
from rdflib.namespace import Namespace, NamespaceManager

from ckanext.dcat.utils import url_to_rdflib_format
from ckanext.dcat.processors import RDFParserException, RDFParser

from profiles import SHACLResultProfile

SHACL = Namespace("http://www.w3.org/ns/shacl#")
SHACL_DIR = os.path.join(os.path.realpath(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), # noqa
    'shacl')
SHACL_OUT_DIR = os.path.join(SHACL_DIR, 'output')


log = logging.getLogger(__name__)


class SwissDCATRDFParser(RDFParser):
    '''
    An RDF to CKAN parser based on rdflib

    Supports different profiles which are the ones that will generate
    CKAN dicts from the RDF graph.
    '''

    def parse(self, data, _format=None,
              page_count=None,
              harvest_source_id=None,
              ech_validation=False,
              shacl_file=None):
        '''
        Parses and RDF graph serialization and into the class graph

        It calls the rdflib parse function with the provided data and format.

        Data is a string with the serialized RDF graph (eg RDF/XML, N3
        ... ). By default RF/XML is expected. The optional parameter _format
        can be used to tell rdflib otherwise.

        It raises a ``RDFParserException`` if there was some error during
        the parsing.

        Returns nothing.
        '''
        _format = url_to_rdflib_format(_format)
        if not _format or _format == 'pretty-xml':
            _format = 'xml'
        try:
            self.g.parse(data=data, format=_format)

        # Apparently there is no single way of catching exceptions from all
        # rdflib parsers at once, so if you use a new one and the parsing
        # exceptions are not cached, add them here.
        # PluginException indicates that an unknown format was passed.
        except (SyntaxError, xml.sax.SAXParseException,
                rdflib.plugin.PluginException, TypeError), e:

            raise RDFParserException(e)

        else:
            if ech_validation:
                datapath, resultpath, shapefilepath = self._datapathes(
                    page_count, harvest_source_id, shacl_file)
                return self._perform_ech_validation(
                    datapath, resultpath, shapefilepath
                )

    def shaclresults(self):
        profile = SHACLResultProfile(self.r)
        return profile.shaclresults()

    def _perform_ech_validation(self, datapath, resultpath, shapefilepath):
        # TODO use pyshacl instead of file-io when
        #      ckan is on python version 3
        with open(datapath, 'w') as datawriter:
            datawriter.write(self.g.serialize(format='turtle'))
        with open(resultpath, 'w') as resultwriter:
            rc = subprocess.call(
                ["/opt/shacl-1.3.0/bin/shaclvalidate.sh",
                 "-datafile", datapath,
                 "-shapesfile", shapefilepath],
                stdout=resultwriter)
        self.r = rdflib.Graph()
        self.r.parse(resultpath, format='n3')
        self.r.bind('sh', SHACL)
        self.r.namespace_manager = NamespaceManager(self.r)
        return rc

    def _datapathes(self, page_count, harvest_source_id, shacl_file):
        harvesterdir = os.path.join(SHACL_OUT_DIR, str(harvest_source_id))
        try:
            os.mkdir(harvesterdir)
        except OSError:
            pass
        datapath = os.path.join(
            SHACL_OUT_DIR, harvesterdir,
            'page-' + str(page_count) + '.ttl')
        shacl_qualifier = shacl_file.split('.')[0]
        resultpath = os.path.join(
            SHACL_OUT_DIR, harvesterdir,
            'page-' + str(page_count) + '.' + shacl_qualifier + '.n3')
        shapefilepath = os.path.join(SHACL_DIR, shacl_file)
        return datapath, resultpath, shapefilepath
