import unittest
from elibrarian_app import create_app, db
from elibrarian_app.models import AuthRole, AuthUser


class AuthUserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing_virtualenv')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        AuthRole.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_model(self):
        duke = AuthUser(email="duke@example.com", username="duke",
                        password="hardcore", confirmed=True)
        adm = AuthUser(email="root@localhost", username="root",
                       password="hardcore", confirmed=True)
        only_usr = AuthUser(username="hidden", password="hid", confirmed=True)

        db.session.add(duke)
        db.session.add(adm)
        db.session.add(only_usr)
        db.session.commit()

        admin_role = AuthRole.query.filter_by(name='administrator').first()
        default_role = AuthRole.query.filter_by(default=True).first()

        only_usr_get = AuthUser.query.filter_by(username="hidden").first()
        self.assertTrue(only_usr_get)
        self.assertEqual(only_usr_get.username, "hidden")
        self.assertEqual(only_usr_get.email, None)
        with self.assertRaises(AttributeError):
            print(only_usr_get.password)
        self.assertEqual(adm.role_id, admin_role.id)
        self.assertTrue(adm.is_administrator())
        self.assertEqual(duke.role_id, default_role.id)

