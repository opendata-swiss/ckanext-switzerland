ckanext-switzerland
===================

CKAN extension for DCAT-AP Switzerland, templates and different plugins for [opendata.swiss](https://opendata.swiss).

## Requirements

- CKAN 2.6+
- ckanext-scheming
- ckanext-fluent

## Update translations

To generate a new ckanext-switzerland.pot file use the following command:

    vagrant ssh
    source /home/vagrant/pyenv/bin/activate
    cd /var/www/ckanext/ckanext-switzerland/
    python setup.py extract_messages

Or follow the official CKAN guide at https://github.com/ckan/ckan/wiki/Translations-and-Extensions

All translations are done via Transifex. To compile the po files use the following command:

## Command

This extension currently provides two paster commands: 
### Command to cleanup the datastore database.
[Datastore currently does not delete tables](https://github.com/ckan/ckan/issues/3422) when the corresponding resource is deleted.
This command finds these orphaned tables and deletes its rows to free the space in the database.
It is meant to be run regularly by a cronjob.

```bash
paster --plugin=ckanext-switzerland ogdch cleanup_datastore -c /var/www/ckan/development.ini
```

### Command to cleanup the harvest jobs.
This commands deletes the harvest jobs and objects per source and overall leaving only the latest n,
where n and the source are optional arguments. The command is supposed to be used in a cron job to 
provide for a regular cleanup of harvest jobs, so that the database is not overloaded with unneeded data
of past job runs. It has a dryrun option so that it can be tested what will get be deleted in the 
database before the actual database changes are performed.

```bash
paster --plugin=ckanext-switzerland ogdch cleanup_harvestjobs [{source_id}] [--keep={n}}] [--dryrun] -c /var/www/ckan/development.ini
```

## Harvesters

### Swiss Dcat Harvester 

The plugin implements a Swiss version of the Dcat Harvester.

### Shacl Validation
The Swiss Dcat Harvester offers a validation where the data is tested against a shacl shape graph.
- the validation currently uses https://jena.apache.org/documentation/shacl/index.html
- the path to the tool and the results should be in the ckan configuration file:
```
ckanext.switzerland.shacl_command_path = /opt/apache-jena-3.13.1/bin/shacl
ckanext.switzerland.shacl_result_path = /home/liipadmin/shaclresults
``` 
- the validation output is reported per harvest source id and harvest job in the result directory
- the results are cleaned up along with the harvestjobs by the command `ogdch cleanup_harvestjobs`, see above.
- the validation is performed when the the harvester is given a configuration parameter `"shacl_validation_file":"<shacl filename>" 
- the possible validation files are in the directoy `dcat/shaclshapes`
- currently the shapes graphs are taken from: https://github.com/factsmission/dcat-ap-ch-shacl.
- the shacl results are displayed as gather errors
- they can also be found in the result directory for the source and job: there the input pages of the harvesters are listed in turtle along with the shacl validation results that is derived per page
- even when the parsing of the shacl validation result fails (the job errors will show this), the results can be accessed in the result directory as turtle.

#### Known issues
- currently the validation is performed my a commandline tool. The parsing of the result from file has sometimes random errors, since the commandline tool sometime produces results that can not be parsed back to python. WHen that occurs, just run the harvest job again.
- when ogdch is upgraded to python3 it should be considered to move to https://github.com/RDFLib/pySHACL for the validation, so that can be directly done in python

#### Known Issues
- ramdomly the parsing of the shacl result of the apache jena report file will fail. 
- Then just repeat and it may go through the next time
- because of this random failures the validation should not be constantly on in production

## Installation

To install ckanext-switzerland:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-switzerland Python package into your virtual environment:

     pip install ckanext-switzerland

3. Add ``switzerland`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload

## Config Settings

This extension uses the following config options (.ini file)

    # the URL of the WordPress AJAX interface
    ckanext.switzerland.wp_ajax_url = https://opendata.swiss/cms/wp-admin/admin-ajax.php

    # number of harvest jobs to keep per harvest source when cleaning up harvest objects   
    ckanext.switzerland.number_harvest_jobs_per_source = 2

    # piwik config
    piwik.site_id = 1
    piwik.url = piwik.opendata.swiss

## Development Installation

To install ckanext-switzerland for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/ogdch/ckanext-switzerland.git
    cd ckanext-switzerland
    python setup.py develop
    pip install -r dev-requirements.txt
    pip install -r requirements.txt

## Update Format-Mapping

To update the Format-Mapping edit the [mapping.yaml](/ckanext/switzerland/mapping.yaml), following the [YAML-Syntax](http://docs.ansible.com/ansible/latest/YAMLSyntax.html). You can check if your changes are valid by pasting the contents of the required changes into a Syntax-Checker, e.g. [YAML Syntax-Checker](http://www.yamllint.com/).
Submit a Pull-Request following our [Contribution-Guidelines](CONTRIBUTING.md).
