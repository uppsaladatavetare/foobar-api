.PHONY: test clean install_requirements setup lint

help:
	@echo 'Available targets:'
	@echo '  lint	Checks the codebase against PEP8 style convention.'
	@echo '  test	Runs all the tests in the project.'
	@echo '  clean	Removes *.pyc files.'
	@echo '  install_requirements Installs local requirements for the project.'
	@echo '  setup Installs requirements and runs project tests.'

lint:
	cd src && flake8 --exclude=migrations,settings .

test:
	cd src && python manage.py test --settings=foobar.settings.test

install_requirements:
	pip install -r requirements/local.txt

setup: install_requirements test

clean:
	find . -name "*.pyc" | xargs rm
