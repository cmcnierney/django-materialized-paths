#!/usr/bin/env python3
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))

CUSTOM_INSTALLED_APPS = (
    'django-materialized-paths',
    'django-materialized-paths.tests',
)


settings.configure(
    SECRET_KEY="django_tests_secret_key",
    DEBUG=False,
    ALLOWED_HOSTS=[],
    INSTALLED_APPS=CUSTOM_INSTALLED_APPS,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    LANGUAGE_CODE='en-us',
    TIME_ZONE='UTC',
    USE_I18N=True,
    USE_L10N=True,
    USE_TZ=True,
)

django.setup()
TestRunner = get_runner(settings)
test_runner = TestRunner()
failures = test_runner.run_tests(["tests"])
sys.exit(bool(failures))
