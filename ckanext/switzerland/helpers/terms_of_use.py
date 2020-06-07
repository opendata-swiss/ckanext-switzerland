"""utils for terms of use"""
import logging
log = logging.getLogger(__name__)

TERMS_OF_USE_OPEN = 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired' # noqa
TERMS_OF_USE_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired' # noqa
TERMS_OF_USE_CLOSED = 'ClosedData'


def simplify_terms_of_use(term_id):
    terms = [
        TERMS_OF_USE_OPEN,
        TERMS_OF_USE_BY,
        TERMS_OF_USE_ASK,
        TERMS_OF_USE_BY_ASK,
    ]

    if term_id in terms:
        return term_id
    return 'ClosedData'
