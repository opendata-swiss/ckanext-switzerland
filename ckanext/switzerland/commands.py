import sys
import itertools
import traceback
import ckan.lib.cli
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk



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
        # - deletes the all harvest jobs and objects except the latest
        # - how many jobs to keep can be set in the ckan config
        paster ogdch cleanup_harvesters [{source_id}]
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):
        # load pylons config
        self._load_config()
        options = {
            'cleanup_datastore': self.cleanup_datastore,
            'help': self.help,
            'cleanup_harvesters': self.cleanup_harvesters,
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

    def cleanup_harvesters(self, source=None):
        """
        command to call the harvester clearing
        :param source: int (optional)
        """
        # get source to clear from arguments
        source_id = None; data_dict = {}
        if len(self.args) >= 2:
            source_id = unicode(self.args[1])
            data_dict['harvest_source_id'] = source_id
            print('clearing for harvest source {}'.format(source_id))
        else:
            print('clearing all harvest sources')

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

        # get configuration
        config_harvest_jobs_name = 'ckanext.switzerland.number_harvest_jobs_per_source'
        config_harvest_jobs_value = tk.config.get(config_harvest_jobs_name, 1)
        try:
            number_of_jobs_to_keep = int(config_harvest_jobs_value)
        except ValueError:
            log.error('Invalid configuration for {}: {}'.format(config_harvest_jobs_name, config_harvest_jobs_value))
            raise ValidationError('Invalid configuration for {}: {}'.format(
                config_harvest_jobs_name, config_harvest_jobs_value))
        else:
            data_dict['number_of_jobs_to_keep'] = number_of_jobs_to_keep

        # perform the clearing
        clearing_result = logic.get_action('ogdch_clean_harvester_jobs')(context, data_dict)

        # print the clearing result
        print('Clearing for harvest sources: {}'.format(','.join(clearing_result['cleared_sources'])))
        print('- deleted {} harvest jobs'.format(clearing_result['deleted_nr_jobs']))
        print('- deleted {} harvest objects'.format(clearing_result['deleted_nr_objects']))
