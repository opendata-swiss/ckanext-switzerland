import os
import shutil

import ckan.plugins.toolkit as tk
from ckan.exceptions import CkanConfigurationException

SHACL_SHAPES_DIR = os.path.join(
    os.path.realpath(os.path.dirname(__file__)),
    'shaclshapes')


def get_shacl_command_from_config():
    shacl_command = tk.config.get('ckanext.switzerland.shacl_command_path')
    if not shacl_command:
        raise CkanConfigurationException(
            """'ckanext.switzerland.shacl_command_path'
            setting is missing in config file""")
    return shacl_command


def get_shacl_resultdir_from_config():
    shacl_result_dir = tk.config.get('ckanext.switzerland.shacl_result_path')
    if not shacl_result_dir:
        raise CkanConfigurationException(
            """'ckanext.switzerland.shacl_result_path'
            setting is missing in config file""")
    return shacl_result_dir


def get_shacl_shapedir():
    return SHACL_SHAPES_DIR


def get_shacl_file_path(resultdir, identifier, format):
    count = 0
    filepath = None
    while not filepath:
        count += 1
        filename = '.'.join([identifier, str(count), format])
        filepath = os.path.join(resultdir, filename)
        if os.path.exists(filepath):
            filepath = None
    return filepath


def clean_shacl_result_dirs(harvest_source_id=None, deleted_jobs_ids=None):
    for harvest_job_id in deleted_jobs_ids:
        job_dir = _get_shacl_result_dir_for_harvest_job(
            harvest_source_id,
            harvest_job_id)
        try:
            shutil.rmtree(job_dir)
        except OSError:
            # if the directory does not exist it is fine
            pass


def get_shacl_shape_file_path(filename):
    shapesdir = get_shacl_shapedir()
    return os.path.join(shapesdir, filename)


def _get_shacl_result_dir_for_harvest_job(harvest_source_id, harvest_job_id):
    return os.path.join(
        get_shacl_resultdir_from_config(),
        harvest_source_id, harvest_job_id)


def make_shacl_result_job_dir(harvest_source_id, harvest_job_id):
    resultdir = _get_shacl_result_dir_for_harvest_job(
        harvest_source_id,
        harvest_job_id)
    try:
        os.makedirs(resultdir)
    except OSError:
        pass
    return resultdir


def _id_short(id):
    return id.split('-')[0]
