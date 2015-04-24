#!/usr/bin/env python
import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include='elibrarian_app/*')
    COV.start()

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
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys

        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('Coverage run results:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        coverage_stats_directory = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=coverage_stats_directory)
        COV.erase()


@manager.command
def resetdb():
    """Upgrade database"""
    from elibrarian_app.models import AuthRole

    print("Starting database upgrade:...")
    upgrade()

    print("Creating basic roles:...")
    AuthRole.insert_roles()


@manager.command
def filldata():
    """Upgrade database and try to import some initial test data"""
    resetdb()
    try:
        # Fixtures intended to exist only at the user computer to quickly fill
        # the database with test or real data.
        from __test_data import load_fixtures
        # The load_fixtures function can be implemented to fill-in the
        # database.
        load_fixtures()
    except ImportError as e:
        print("Fixtures data not found, load skipped. | Error: {0}".format(e))


if __name__ == '__main__':
    print("Running with config: {0}".format(config_name))
    manager.run()
