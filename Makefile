TARGET?=tests

test:
	DJANGO_SETTINGS_MODULE=tests.settings PYTHONPATH=".:src" django-admin.py test ${TARGET} -v2

coverage:
	coverage erase
	PYTHONPATH="." coverage run --source='src' src/manage.py test tests --settings "tests.settings"
	coverage report