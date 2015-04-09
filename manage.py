#!/usr/bin/env python
import os
from elibrarian_app import create_app, db
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Shell

config_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name)
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def resetdb():
    print("Dropping database:...")
    db.drop_all()

    print("Recreating models:...")
    db.create_all()


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
