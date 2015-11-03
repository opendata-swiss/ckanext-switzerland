#!/bin/bash

HERE=`dirname $0`
msgcat --use-first \
    "$HERE/../i18n/de/LC_MESSAGES/ckanext.po" \
    "$HERE/../../../ckan/ckan/i18n/de/LC_MESSAGES/ckan.po" \
    | msgfmt - -o "$HERE/../../../ckan/ckan/i18n/de/LC_MESSAGES/ckan.mo"
msgcat --use-first \
    "$HERE/../i18n/fr/LC_MESSAGES/ckanext.po" \
    "$HERE/../../../ckan/ckan/i18n/fr/LC_MESSAGES/ckan.po" \
    | msgfmt - -o "$HERE/../../../ckan/ckan/i18n/fr/LC_MESSAGES/ckan.mo"
msgcat --use-first \
    "$HERE/../i18n/it/LC_MESSAGES/ckanext.po" \
    "$HERE/../../../ckan/ckan/i18n/it/LC_MESSAGES/ckan.po" \
    | msgfmt - -o "$HERE/../../../ckan/ckan/i18n/it/LC_MESSAGES/ckan.mo"
