import unittest
from flask import current_app, url_for
from elibrarian_app import create_app, db


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing_virtualenv')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        with current_app.test_request_context('/'):
            self.root_ext_lnk = url_for('main.index', _external=True)
            self.ui_ext_lnk = url_for('webui.index', _external=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])

    def test_landing_page(self):
        # we redirect from root to UI blueprint
        response = self.client.get(self.root_ext_lnk)
        self.assertTrue(response.status_code == 302)

        # trying to get UI landing page
        response = self.client.get(self.ui_ext_lnk)
        self.assertTrue(response.status_code == 200)
