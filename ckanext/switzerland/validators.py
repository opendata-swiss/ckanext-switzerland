from ckan.plugins.toolkit import missing, _
import ckan.lib.navl.dictization_functions as df
from ckanext.scheming.validation import scheming_validator
import json
import pprint

@scheming_validator
def multiple_text(field, schema):
    """
    Accept zero or more values as a list and convert
    to a json list for storage:
    1. a list of strings, eg.:
       ["somevalue a", "somevalue -b"]
    2. a single string for single item selection in form submissions:
       "somevalue-a"
    """
    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        # if errors[key]:
        #     return

        value = data[key]
        if value is not missing:
            if isinstance(value, basestring):
                value = [value]
            elif not isinstance(value, list):
                errors[key].append(_('expecting list of strings, got "%s"') % str(value) )
                return
        else:
            value = []

        if not errors[key]:
            data[key] = json.dumps(value)

    return validator

@scheming_validator
def list_of_dicts(field, schema):
    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        try: 
            data_dict = df.unflatten(data[('__junk',)])
            value = data_dict[key[0]]
            if value is not missing:
                if isinstance(value, basestring):
                    value = [value]
                elif not isinstance(value, list):
                    errors[key].append(_('expecting list of strings, got "%s"') % str(value) )
                    return
            else:
                value = []

            if not errors[key]:
                data[key] = json.dumps(value)

            # remove from junk
            del data_dict[key[0]]
            data[('__junk',)] = df.flatten_dict(data_dict)
        except KeyError:
            pass

    return validator

def multiple_text_output(value):
    """
    Return stored json representation as a list
    """
    try:
        return json.loads(value)
    except ValueError:
        return [value]
