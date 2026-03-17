# Запустить линтер
lint:
	pylint $(shell git ls-files '*.py' | grep -v 'migrations/')