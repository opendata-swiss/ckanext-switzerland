"""
helpers for preparing the resource format
belong in this file
"""
import yaml
import os
import urlparse

__location__ = os.path.realpath(os.path.join(
    os.getcwd(),
    os.path.dirname(__file__))
)


class FormatMappingNotLoadedError(Exception):
    pass


def ogdch_get_format_mapping():
    """gets the format mapping from  a file for ogdch controller plugins"""
    try:
        mapping_path = os.path.join(__location__, 'mapping.yaml')
        with open(mapping_path, 'r') as format_mapping_file:
            format_mapping = yaml.safe_load(format_mapping_file)
    except (IOError, yaml.YAMLError) as exception:
        raise FormatMappingNotLoadedError(
            'Loading Format-Mapping from Path: (%s) '
            'failed with Exception: (%s)'
            % (mapping_path, exception)
        )
    else:
        return format_mapping


# Generates format of resource and saves it in format field
def prepare_resource_format(resource, format_mapping):
    resource_format = ''

    # get format from media_type field if available
    if not resource_format and resource.get('media_type'):  # noqa
        resource_format = resource['media_type'].split('/')[-1].lower()

    # get format from format field if available (lol)
    if not resource_format and resource.get('format'):
        resource_format = resource['format'].split('/')[-1].lower()

    # check if 'media_type' or 'format' can be mapped
    has_format = (_map_to_valid_format(
        resource_format,
        format_mapping
    ) is not None)

    # if the fields can't be mapped,
    # try to parse the download_url as a last resort
    if not has_format and resource.get('download_url'):
        path = urlparse.urlparse(resource['download_url']).path
        ext = os.path.splitext(path)[1]
        if ext:
            resource_format = ext.replace('.', '').lower()

    mapped_format = _map_to_valid_format(
        resource_format,
        format_mapping
    )
    if mapped_format:
        # if format could be successfully mapped write it to format field
        resource['format'] = mapped_format
    elif not resource.get('download_url'):
        resource['format'] = 'SERVICE'
    else:
        # else return empty string (this will be indexed as N/A)
        resource['format'] = ''

    # if format could not be mapped and media_type exists use this value  # noqa
    if (not resource.get('format') and resource.get('media_type')):
        resource['format'] = resource['media_type'].split('/')[-1]

    return resource


def prepare_formats_for_index(resources, format_mapping):
    """generates a set with formats of all resources"""
    formats = set()
    for r in resources:
        resource = prepare_resource_format(
            resource=r,
            format_mapping=format_mapping
        )
        if resource['format']:
            formats.add(resource['format'])
        else:
            formats.add('N/A')

    return list(formats)


# all formats that need to be mapped have to be entered in the mapping.yaml
def _map_to_valid_format(resource_format, format_mapping):
    resource_format_lower = resource_format.lower()
    for key, values in format_mapping.iteritems():
        if resource_format_lower in values:
            return key
    else:
        return None
