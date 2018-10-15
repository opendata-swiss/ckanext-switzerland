import nose

from ckan.lib.helpers import url_for
import ckan.plugins.toolkit as tk
import ckan.model as model

from ckan.tests import helpers, factories

assert_equal = nose.tools.assert_equal
assert_true = nose.tools.assert_true

class TestController(helpers.FunctionalTestBase):

    @classmethod
    def teardown_class(cls):
        super(TestController, cls).teardown_class()
        helpers.reset_db()

    def setup(self):
        super(TestController, self).setup()
        user = tk.get_action('get_site_user')({'ignore_auth': True})['name']
        context = {'model': model, 'session': model.Session,
                   'user': user, 'ignore_auth': True}
        # create an org
        self.org = {
            'name': 'test-org',
            'title': {
                'de': 'Test Org DE',
                'fr': 'Test Org FR',
                'it': 'Test Org IT',
                'en': 'Test Org EN',
            }
        }
        tk.get_action('organization_create')(context, self.org)

        # create a valid DCAT-AP Switzerland compliant dataset
	self.dataset = {
	   'coverage':'',
	   'issued':'2015-09-08T00:00:00',
	   'contact_points':[{'email':'pierre@bar.ch', 'name':'Pierre'}],
	   'keywords':{
	      'fr':[],
	      'de':[],
	      'en':[],
	      'it':[] 
	   },
	   'spatial':'',
	   'publishers':[{'label':'Bundesarchiv'}],
	   'description':{
	      'fr': 'Description FR',
	      'de': 'Beschreibung DE',
	      'en': 'Description EN',
	      'it': 'Description IT'
	   },
	   'title':{
	      'fr': 'FR Test',
	      'de': 'DE Test',
	      'en': 'EN Test',
	      'it': 'IT Test'
	   },
	   'language':[
	      'en',
	      'de'
	   ],
	   'name':'test-dataset',
	   'relations': [],
	   'see_alsos': [],
	   'temporals': [],
	   'accrual_periodicity':'http://purl.org/cld/freq/completelyIrregular',
	   'modified':'2015-09-09T00:00:00',
	   'url':'',
           'owner_org': 'test-org',
	   'identifier':'test@test-org'
	}
        tk.get_action('package_create')(context, self.dataset)


    def test_valid_redirect(self):

        app = self._get_test_app()

        url = url_for('perma_redirect', id=self.dataset['identifier'])
        assert_equal(url, '/perma/test%40test-org')

        response = app.get(url)
        assert_equal(response.status_int, 302)
        assert_equal(response.headers.get('Location'), 'http://test.ckan.net/dataset/test-dataset')

    def test_invalid_redirect(self):

        app = self._get_test_app()

        url = url_for('perma_redirect', id='non-existent-id@unknown')
        assert_equal(url, '/perma/non-existent-id%40unknown')

        # expect a 404 response
        response = app.get(url, status=404)

    def test_org_list_links(self):
        app = self._get_test_app()

        # no locale, should default to EN
        url = url_for('organizations_index')
        assert url.startswith('/organization'), "URL does not start with /organization"

        response = app.get(url, status=200)

        assert '/en/organization/test-org' in response

        # set locale via CKAN_LANG to IT
        url = url_for('organizations_index')
        assert_equal(url, '/organization')

        response = app.get(url, status=200, extra_environ={'CKAN_LANG': 'it', 'CKAN_CURRENT_URL': url})

        assert '/it/organization/test-org' in response

        # locale DE
        url = url_for('organizations_index', locale='de')
        assert_equal(url, '/de/organization')

        response = app.get(url, status=200)

        assert '/de/organization/test-org' in response

        # locale FR
        url = url_for('organizations_index', locale='fr')
        assert_equal(url, '/fr/organization')

        response = app.get(url, status=200)

        assert '/fr/organization/test-org' in response

