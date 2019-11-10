from __future__ import print_function

import xml
import logging
import subprocess

import rdflib
import rdflib.parser
from rdflib.namespace import NamespaceManager

from ckanext.dcat.utils import url_to_rdflib_format
from ckanext.dcat.processors import RDFParserException, RDFParser

from profiles import SHACLResultProfile, SHACL
import helpers as tk_dcat

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
              harvest_job_id=None,
              shacl_validation=False,
              shacl_file=None):
        '''
        Parses and RDF graph serialization and into the class graph

        It calls the rdflib parse function with the provided data and format.

        Data is a string with the serialized RDF graph (eg RDF/XML, N3
        ... ). By default RF/XML is expected. The optional parameter _format
        can be used to tell rdflib otherwise.

        It raises a ``RDFParserException`` if there was some error during
        the parsing.

        Returns a return code in case of shacl graph validation
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
            if shacl_validation:
                self._perform_shacl_validation(
                    harvest_source_id, harvest_job_id, page_count, shacl_file)

    def _perform_shacl_validation(
            self, harvest_source_id, harvest_job_id, page_count, shacl_file):
        """the graph  is written to a file and then validated with
        the shacl file. This validation is currently performed by a
        shell command. Therefore the result is again a file, that
         is then read into an rdflib graph"""
        # TODO use pyshacl instead of file-io when
        #      ckan is on python version 3
        shacl_command = tk_dcat.get_shacl_command_from_config()

        datapath = tk_dcat.get_shacl_data_file_path(
            harvest_source_id, harvest_job_id, page_count, 'ttl')

        resultpath = tk_dcat.get_shacl_result_file_path(
            harvest_source_id, harvest_job_id, page_count, shacl_file, 'ttl')

        shapefilepath = tk_dcat.get_shacl_shape_file_path(shacl_file)

        log.debug("SHACL performing shacl evaluation: evaluating {} against {}"
                  .format(datapath, shacl_file))

        with open(datapath, 'w') as datawriter:
            datawriter.write(self.g.serialize(format='turtle'))
        log.debug("SHACL data serialized as turtle: {}"
                  .format(datapath))
        with open(resultpath, 'w') as resultwriter:
            subprocess.call(
                [shacl_command,
                 "validate",
                 "--shapes", shapefilepath,
                 "--data", datapath],
                stdout=resultwriter)
        try:
            self.r = rdflib.Graph()
            self.r.parse(resultpath, format='ttl')
        except (SyntaxError, xml.sax.SAXParseException,
                rdflib.plugin.PluginException, TypeError), e:

            raise RDFParserException(e)
        log.debug(
            "SHACL result graph parsed for page {}: length: {}"
            .format(page_count, len(self.r)))
        self.r.bind('sh', SHACL)
        self.r.namespace_manager = NamespaceManager(self.r)

    def shaclresults_grouped(self):
        """get shacl results"""
        profile = SHACLResultProfile(self.r)
        log.debug("SHACL profile set and getting results: {}".format(profile))
        return profile.shaclresults_grouped_by_node()
