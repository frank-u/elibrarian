import unittest
from elibrarian_app import create_app, db
from elibrarian_app.models import Author


class AuthorModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing_virtualenv')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_model(self):
        author = Author()
        self.assertTrue(author.original_lang is None)
