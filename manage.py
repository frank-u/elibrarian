#!/usr/bin/env python
import os
from elibrarian_app import create_app, db
from elibrarian_app.models import AuthRole, AuthUser, AuthUserPersonalLibrary, \
    Author, AuthorDetail, Authors2LiteraryWorks, \
    BookGenreSnap, BookSeries, BookSeriesDetail, BookSeriesSnap, Genre, \
    GenreDetail, LiteraryWork, LiteraryWorkStorage
from flask.ext.migrate import Migrate, MigrateCommand, upgrade
from flask.ext.script import Manager, Shell

config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name)
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, AuthRole=AuthRole, AuthUser=AuthUser,
                AuthUserPersonalLibrary=AuthUserPersonalLibrary,
                Author=Author, AuthorDetail=AuthorDetail,
                Authors2LiteraryWorks=Authors2LiteraryWorks,
                BookGenreSnap=BookGenreSnap, BookSeries=BookSeries,
                BookSeriesDetail=BookSeriesDetail,
                BookSeriesSnap=BookSeriesSnap, Genre=Genre,
                GenreDetail=GenreDetail, LiteraryWork=LiteraryWork,
                LiteraryWorkStorage=LiteraryWorkStorage)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def resetdb():
    from elibrarian_app.models import AuthRole

    print("Starting database upgrade:...")
    upgrade()

    print("Creating basic roles:...")
    AuthRole.insert_roles()


@manager.command
def filldata():
    resetdb()
    try:
        #   Fixtures intended to exist only at the user computer to quickly fill
        # the database with test or real data.
        from __test_data import load_fixtures
        #   The load_fixtures function can be implemented to fill-in the
        # database.
        load_fixtures()
    except ImportError as e:
        print("Fixtures data not found, load skipped. | Error: {0}".format(e))


if __name__ == '__main__':
    print("Running with config: {0}".format(config_name))
    manager.run()
