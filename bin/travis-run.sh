#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check PEP-8 code style and McCabe complexity
flake8 --statistics --show-source ckanext

# run tests
nosetests --verbose ckanext/switzerland
