.PHONY: test clean

help:
	@echo 'Available targets:'
	@echo '  lint	Checks the codebase against PEP8 style convention.'
	@echo '  test	Runs all the tests in the project.'
	@echo '  clean	Removes *.pyc files.'

lint:
	cd src && flake8 --exclude=migrations .

test:
	cd src && python manage.py test --settings=foobar.settings.test

clean:
	find . -name "*.pyc" | xargs rm
