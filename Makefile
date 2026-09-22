.PHONY: test frontend-install frontend-build check

test:
	python3 -m unittest discover tests

frontend-install:
	npm --prefix studio ci

frontend-build: frontend-install
	npm --prefix studio run build

check: test frontend-build
