import unittest
from base64 import b64encode
from elibrarian_app import create_app, db
from elibrarian_app.models import AuthRole, AuthUser, Author, AuthorDetail, \
    LiteraryWork, LiteraryWorkDetail
from flask import current_app, url_for
from json import loads


class RESTAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing_virtualenv')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        AuthRole.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def generate_auth_header(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_root_route(self):
        response = self.client.get(
            url_for('api.index')
        )
        self.assertTrue(response.status_code == 200)

    def test_auth_roles(self):
        role_admin = AuthRole.query.filter_by(name='administrator').first()
        self.assertTrue(role_admin.permissions == 255)

    def test_pagination(self):
        admin_role = AuthRole.query.filter_by(name='administrator').first()
        duke = AuthUser(email="duke@example.com", username="duke",
                        password="hardcore", confirmed=True,
                        role=admin_role)
        db.session.add(duke)
        db.session.commit()

        # add one author and many books
        author1 = Author()
        db.session.add(author1)

        author1_details = AuthorDetail()
        author1_details.lang = "en"
        author1_details.last_name = "London"
        author1_details.first_name = "Jack"

        author1.details.append(author1_details)

        for i in range(100):
            lw = LiteraryWork()
            lw.original_lang = "en"
            lw.creation_datestring = "1910"
            db.session.add(lw)

            lwd = LiteraryWorkDetail()
            lwd.lang = "en"
            lwd.title = "Burning Daylight"

            lw.details.append(lwd)
        db.session.commit()

        # test page 1
        response = self.client.get(
            url_for('api.get_literary_works'),
            headers=self.generate_auth_header("duke@example.com", "hardcore")
        )
        json_response = loads(response.data.decode('utf-8'))
        self.assertTrue(json_response["_meta"]["total"] == 100)
        self.assertTrue(json_response["_meta"]["page"] == 1)
        self.assertTrue(json_response["_meta"]["max_results"] ==
                        current_app.config['ELIBRARIAN_ITEMS_PER_PAGE'])
        self.assertTrue(json_response["_links"]["next"] ==
                        url_for('api.get_literary_works',
                                page=2, _external=True))
        self.assertTrue(json_response["_links"]["parent"]["href"] ==
                        url_for('api.index', _external=True))
        self.assertTrue(json_response["_links"]["self"]["href"] ==
                        url_for('api.get_literary_works', _external=True))
        self.assertTrue(response.status_code == 200)

        response2 = self.client.get(
            url_for('api.get_literary_works', page=2),
            headers=self.generate_auth_header("duke@example.com", "hardcore")
        )
        json_response2 = loads(response2.data.decode('utf-8'))
        self.assertTrue(json_response2["_meta"]["total"] == 100)
        self.assertTrue(json_response2["_meta"]["page"] == 2)
        self.assertTrue(json_response2["_links"]["next"] ==
                        url_for('api.get_literary_works',
                                page=3, _external=True))
        self.assertTrue(json_response2["_links"]["prev"] ==
                        url_for('api.get_literary_works',
                                page=1, _external=True))
        self.assertTrue(response2.status_code == 200)

    def test_get_literary_works(self):
        admin_role = AuthRole.query.filter_by(name='administrator').first()
        duke = AuthUser(email="duke@example.com", username="duke",
                        password="hardcore", confirmed=True,
                        role=admin_role)
        db.session.add(duke)
        db.session.commit()
        duke_id = duke.id

        get_user = AuthUser.query.filter_by(id=duke_id).first()
        self.assertTrue(get_user.id == duke_id)

        # get without login
        response = self.client.get(
            url_for('api.get_literary_works')
        )
        self.assertTrue(response.status_code == 403)
        self.assertTrue('Insufficient permissions' in
                        response.get_data(as_text=True))

        # get with invalid login
        response = self.client.get(
            url_for('api.get_literary_works'),
            headers=self.generate_auth_header("duke", "nightmare")
        )
        self.assertTrue(response.status_code == 401)
        self.assertTrue('Invalid credentials' in
                        response.get_data(as_text=True))

        # get with valid login
        response = self.client.get(
            url_for('api.get_literary_works'),
            headers=self.generate_auth_header("duke@example.com", "hardcore")
        )
        json_response = loads(response.data.decode('utf-8'))
        self.assertTrue(json_response["_meta"]["total"] == 0)
        self.assertTrue(json_response["_items"] == [])
        self.assertTrue(response.status_code == 200)

        # add one author
        author1 = Author()
        db.session.add(author1)

        author1_details = AuthorDetail()
        author1_details.lang = "en"
        author1_details.last_name = "London"
        author1_details.first_name = "Jack"

        author1.details.append(author1_details)

        lw = LiteraryWork()
        lw.original_lang = "en"
        lw.creation_datestring = "1910"
        db.session.add(lw)

        lwd = LiteraryWorkDetail()
        lwd.lang = "en"
        lwd.title = "Burning Daylight"

        lw.details.append(lwd)
        db.session.commit()

        # get with valid login and some data
        response = self.client.get(
            url_for('api.get_literary_works'),
            headers=self.generate_auth_header("duke@example.com", "hardcore")
        )
        json_response = loads(response.data.decode('utf-8'))
        self.assertTrue(json_response["_meta"]["page"] == 1)
        self.assertTrue(json_response["_meta"]["total"] == 1)
        self.assertTrue("prev" not in json_response["_links"].keys())
        self.assertTrue("next" not in json_response["_links"].keys())
        self.assertTrue(json_response["_items"] != [])
        self.assertTrue(response.status_code == 200)

    def test_get_literary_work(self):
        admin_role = AuthRole.query.filter_by(name='administrator').first()
        duke = AuthUser(email="duke@example.com", username="duke",
                        password="hardcore", confirmed=True,
                        role=admin_role)
        db.session.add(duke)

        author1 = Author()
        db.session.add(author1)

        author1_details = AuthorDetail()
        author1_details.lang = "en"
        author1_details.last_name = "London"
        author1_details.first_name = "Jack"

        author1.details.append(author1_details)
        db.session.commit()

        lw = LiteraryWork()
        lw.original_lang = "en"
        lw.creation_datestring = "1910"
        db.session.add(lw)

        lwd = LiteraryWorkDetail()
        lwd.lang = "en"
        lwd.title = "Burning Daylight"

        lw.details.append(lwd)
        author1.literary_works.append(lw)
        db.session.commit()

        # get with valid login and some data
        response = self.client.get(
            url_for('api.get_literary_work', work_id=lw.id, _external=True),
            headers=self.generate_auth_header("duke@example.com", "hardcore")
        )
        json_response = loads(response.data.decode('utf-8'))
        #self.assertTrue(json_response["authors"][0]["id"] == author1.id)
        #self.assertTrue(json_response["authors"][0]["name"] == "Jack London")
        #self.assertTrue(json_response["authors"][0]["url"] ==
        #                url_for('api.get_author', author_id=author1.id,
        #                        _external=True))
        #self.assertTrue(json_response["id"] == lw.id)
        #self.assertTrue(json_response["original_lang"] == "en")
        #self.assertTrue(json_response["url"] ==
        #                url_for('api.get_literary_work',
        #                        work_id=lw.id, _external=True))
        self.assertTrue(response.status_code == 200)
