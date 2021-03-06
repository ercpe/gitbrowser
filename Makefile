TARGET?=tests

test_default_python:
	@python --version
	DJANGO_SETTINGS_MODULE=tests.settings PYTHONPATH=".:src" src/manage.py test -v2

test_py2:
	@python --version
	DJANGO_SETTINGS_MODULE=tests.settings PYTHONPATH=".:src" python2 src/manage.py test -v2

test_py3:
	@python --version
	DJANGO_SETTINGS_MODULE=tests.settings PYTHONPATH=".:src" python3 src/manage.py test -v2

test: test_py2 test_py3

compile:
	@echo Compiling python code
	python -m compileall src/

compile_optimized:
	@echo Compiling python code optimized
	python -O -m compileall src/

coverage:
	@python --version
	coverage erase
	DJANGO_SETTINGS_MODULE=tests.settings PYTHONPATH=".:src" coverage run --source='src' src/manage.py test -v2
	coverage report

sonar:
	/usr/local/bin/sonar-scanner/bin/sonar-scanner

clean:
	find -name "*.py?" -or -name "coverage.xml" -or -name "testresults.xml" -delete
	rm -fr htmlcov dist *.egg-info

travis: compile compile_optimized test_default_python coverage
jenkins: travis sonar
