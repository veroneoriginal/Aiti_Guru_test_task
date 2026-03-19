# Запустить линтер
lint:
	pylint $(shell git ls-files '*.py' | grep -v 'migrations/')

test:
	pytest tests/ -v

ref:
	isort .
	make lint
	make test
