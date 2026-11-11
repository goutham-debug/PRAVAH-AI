"""Production-safety guards. Needs no database. Run: python -m unittest tests.test_config_guards"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
from config import Config  # noqa: E402

KEY = 'k' * 40
PG = 'postgresql+psycopg2://u:p@db.example.test:5432/postgres'


def patched(**kw):
    return mock.patch.multiple(Config, **kw)


class ConfigGuardTests(unittest.TestCase):
    def test_short_secret_rejected(self):
        with patched(SECRET_KEY='short'), self.assertRaises(RuntimeError):
            Config.validate()

    def test_production_refuses_sqlite(self):
        with patched(SECRET_KEY=KEY, ENV='production', SQLALCHEMY_DATABASE_URI='sqlite:///x.db', LOAD_PILOT_DATASET=False):
            with self.assertRaisesRegex(RuntimeError, 'SQLite'):
                Config.validate()

    def test_production_refuses_quarantined_dev_data(self):
        with patched(SECRET_KEY=KEY, ENV='production', SQLALCHEMY_DATABASE_URI=PG, LOAD_PILOT_DATASET=True):
            with self.assertRaisesRegex(RuntimeError, 'LOAD_PILOT_DATASET'):
                Config.validate()

    def test_production_postgres_ok(self):
        with patched(SECRET_KEY=KEY, ENV='production', SQLALCHEMY_DATABASE_URI=PG, LOAD_PILOT_DATASET=False):
            Config.validate()

    def test_development_sqlite_allowed(self):
        with patched(SECRET_KEY=KEY, ENV='development', SQLALCHEMY_DATABASE_URI='sqlite:///x.db'):
            Config.validate()

    def test_pilot_dataset_defaults_off(self):
        import os
        if 'LOAD_PILOT_DATASET' not in os.environ:
            self.assertFalse(Config.LOAD_PILOT_DATASET)


if __name__ == '__main__':
    unittest.main()
