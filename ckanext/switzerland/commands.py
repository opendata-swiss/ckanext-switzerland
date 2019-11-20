import sys
import os
import itertools
import traceback
import ckan.lib.cli
import ckan.logic as logic
import ckan.model as model
import helpers as ogdch_helpers


class OgdchCommand(ckan.lib.cli.CkanCommand):
    '''Command for opendata.swiss
    Usage:
        # General usage
        paster --plugin=ckanext-switzerland <command> -c <path to config file>

        # Show this help
        paster ogdch help

        # Cleanup datastore
        paster ogdch cleanup_datastore

        # Cleanup harvester jobs and objects:
        # - deletes all the harvest jobs and objects except the latest n
        # - the default number of jobs to keep is 10
        # - the command can be performed with a dryrun option where the
        #   database will remain unchainged

        paster ogdch cleanup_harvestjobs
            [{source_id}] [--keep={n}}] [--dryrun}]
        # Shacl validate harvest source
        # - validates a harvest source against a shacl shape file
        # - output a csv file of shacl shape validation errors
        # - the command can be performed with a verbose option where
        #   also the data and the data results remain, so that it can be
        #   hand checked if wanted
        # - the shape file is expected in the shaclshape directory
        # - the results are written in the shaclresults directory
        # - both of these directories are specified in the ckan
        #   configuration file

        paster ogdch shacl_validate
            {source_id} --shape={name of the shape file}
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(ckan.lib.cli.CkanCommand, self).__init__(name)
        self.parser.add_option(
            '--keep', action="store", type="int", dest='nr_of_jobs_to_keep',
            default=10,
            help='The number of latest harvest jobs to keep')
        self.parser.add_option(
            '--dryrun', action="store_true", dest='dryrun',
            default=False,
            help='dryrun of cleanup harvestjobs')
        self.parser.add_option(
            '--shapefile', action="store_true", dest='shapefile',
            default='ech-0200.shacl.ttl',
            help='shaclshape file name for shacl shape validation')

    def command(self):
        # load pylons config
        self._load_config()
        options = {
            'cleanup_datastore': self.cleanup_datastore,
            'help': self.help,
            'cleanup_harvestjobs': self.cleanup_harvestjobs,
            'shacl_validate': self.shacl_validate,
        }

        try:
            cmd = self.args[0]
            options[cmd](*self.args[1:])
        except KeyError:
            self.help()
            sys.exit(1)

    def help(self):
        print(self.__doc__)

    def cleanup_datastore(self):
        user = logic.get_action('get_site_user')({'ignore_auth': True}, {})
        context = {
            'model': model,
            'session': model.Session,
            'user': user['name']
        }
        try:
            logic.check_access('datastore_delete', context)
            logic.check_access('resource_show', context)
        except logic.NotAuthorized:
            print("User is not authorized to perform this action.")
            sys.exit(1)

        # query datastore to get all resources from the _table_metadata
        resource_id_list = []
        try:
            for offset in itertools.count(start=0, step=100):
                print(
                    "Load metadata records from datastore (offset: %s)"
                    % offset
                )
                record_list, has_next_page = self._get_datastore_table_page(context, offset)  # noqa
                resource_id_list.extend(record_list)
                if not has_next_page:
                    break
        except Exception, e:
            print(
                "Error while gathering resources: %s / %s"
                % (str(e), traceback.format_exc())
            )

        # delete the rows of the orphaned datastore tables
        delete_count = 0
        for resource_id in resource_id_list:
            logic.check_access('datastore_delete', context)
            logic.get_action('datastore_delete')(
                context,
                {'resource_id': resource_id, 'force': True}
            )
            print("Table '%s' deleted (not dropped)" % resource_id)
            delete_count += 1

        print("Deleted content of %s tables" % delete_count)

    def _get_datastore_table_page(self, context, offset=0):
        # query datastore to get all resources from the _table_metadata
        result = logic.get_action('datastore_search')(
            context,
            {
                'resource_id': '_table_metadata',
                'offset': offset
            }
        )

        resource_id_list = []
        for record in result['records']:
            try:
                # ignore 'alias' records
                if record['alias_of']:
                    continue

                logic.check_access('resource_show', context)
                logic.get_action('resource_show')(
                    context,
                    {'id': record['name']}
                )
                print("Resource '%s' found" % record['name'])
            except logic.NotFound:
                resource_id_list.append(record['name'])
                print("Resource '%s' *not* found" % record['name'])
            except logic.NotAuthorized:
                print("User is not authorized to perform this action.")
            except (KeyError, AttributeError), e:
                print("Error while handling record %s: %s" % (record, str(e)))
                continue

        # are there more records?
        has_next_page = (len(result['records']) > 0)

        return (resource_id_list, has_next_page)

    def cleanup_harvestjobs(self, source=None):
        """
        command for the harvester job cleanup
        :argument source: string (optional)
        :argument number_of_jobs_to_keep: int (optional)
        """
        # get source from arguments
        source_id = None
        data_dict = {}
        if len(self.args) >= 2:
            source_id = unicode(self.args[1])
            data_dict['harvest_source_id'] = source_id
            print('cleaning up jobs for harvest source {}'.format(source_id))
        else:
            print('cleaning up jobs for all harvest sources')

        # get named arguments
        data_dict['number_of_jobs_to_keep'] = self.options.nr_of_jobs_to_keep
        data_dict['dryrun'] = self.options.dryrun

        # set context
        context = {'model': model,
                   'session': model.Session,
                   'ignore_auth': True}
        admin_user = logic.get_action('get_site_user')(context, {})
        context['user'] = admin_user['name']

        # test authorization
        try:
            logic.check_access('harvest_sources_clear', context, data_dict)
        except logic.NotAuthorized:
            print("User is not authorized to perform this action.")
            sys.exit(1)

        # perform the harvest job cleanup
        result = logic.get_action(
            'ogdch_cleanup_harvestjobs')(context, data_dict)

        # print the result of the harvest job cleanup
        self._print_clean_harvestjobs_result(result, data_dict)

    def _print_clean_harvestjobs_result(self, result, data_dict):
        print('\nCleaning up jobs for harvest sources:\n{}\nConfiguration:'
              .format(37 * '-'))
        self._print_configuration(data_dict)
        print('\nResults per source:\n{}'.format(19 * '-'))
        for source in result['sources']:
            if source.id in result['cleanup'].keys():
                self._print_harvest_source(source)
                self._print_cleanup_result_per_source(
                    result['cleanup'][source.id])
            else:
                self._print_harvest_source(source)
                print('Nothing needs to be done for this source')

        if data_dict['dryrun']:
            print('\nThis has been a dry run: '
                  'if you want to perfom these changes'
                  ' run this again without the option --dryrun!')
        else:
            print('\nThe database has been cleaned from harvester '
                  'jobs and harvester objects.'
                  ' See above about what has been done.')

    def _print_harvest_source(self, source):
        print('\n           Source id: {0}'.format(source.id))
        print('                 url: {0}'.format(source.url))
        print('                type: {0}'.format(source.type))

    def _print_cleanup_result_per_source(self, cleanup_result):
        print('   nr jobs to delete: {0}'
              .format(len(cleanup_result['deleted_jobs'])))
        print('nr objects to delete: {0}'
              .format(cleanup_result['deleted_nr_objects']))
        print('      jobs to delete:')
        self._print_harvest_jobs(cleanup_result['deleted_jobs'])

    def _print_configuration(self, data_dict):
        for k, v in data_dict.items():
            print '- {}: {}'.format(k, v)

    def _print_harvest_jobs(self, jobs):
        header_list = ["id", "created", "status"]
        row_format = "{:<20}|{:<40}|{:<20}|{:<20}"
        print(row_format.format('', *header_list))
        print('{:<20}+{:<40}+{:<20}+{:<20}'
              .format('', '-' * 40, '-' * 20, '-' * 20))
        for job in jobs:
            print(row_format
                  .format('',
                          job.id,
                          job.created.strftime('%Y-%m-%d %H:%M:%S'),
                          job.status))

    def shacl_validate(self, source=None):
        """
        command for the harvester job cleanup
        :argument source: string (optional)
        """
        # checking arguments
        data_dict = {}
        print('\nCommand Shacl Validation:\n')
        if len(self.args) >= 2:
            source_id = unicode(self.args[1])
        else:
            print('- Aborting: Please provide a harvest source')
            sys.exit(1)

        if not self.options.shapefile:
            print('- Aborting: Please provide a shapefile name')
            sys.exit(1)

        shapedir = ogdch_helpers.get_shacl_shapesdir_from_config()
        shapefilepath = os.path.join(
            shapedir, self.options.shapefile)
        if not os.path.exists(shapefilepath):
            print('Shacl shape file does not exist in path {}'
                  .format(shapefilepath))
            sys.exit(1)

        # loading arguments into config
        data_dict['harvest_source_id'] = source_id
        data_dict['shapefile'] = self.options.shapefile

        # setting up other filepathes
        data_dict['shapefilepath'] = shapefilepath
        data_dict['resultdir'] = \
            ogdch_helpers.make_shacl_results_dir(source_id)
        data_dict['shaclcommand'] = \
            ogdch_helpers.get_shacl_command_from_config()
        data_dict['datapath'] = ogdch_helpers.get_shacl_file_path(
            data_dict['resultdir'], 'data', 'ttl')
        data_dict['resultpath'] = ogdch_helpers.get_shacl_file_path(
            data_dict['resultdir'], 'result', 'ttl')
        data_dict['csvpath'] = ogdch_helpers.get_shacl_file_path(
            data_dict['resultdir'], 'result', 'csv')

        # set context
        context = {'model': model,
                   'session': model.Session,
                   'ignore_auth': True}
        admin_user = logic.get_action('get_site_user')(context, {})
        context['user'] = admin_user['name']

        # test authorization
        try:
            logic.check_access('harvest_sources_clear', context, data_dict)
        except logic.NotAuthorized:
            print("User is not authorized to perform this action.")
            sys.exit(1)

        # perform shacl validation
        logic.get_action(
            'ogdch_shacl_validate')(context, data_dict)
