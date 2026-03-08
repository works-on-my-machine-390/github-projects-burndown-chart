PYTHON := python

ifeq ($(OS),Windows_NT)
ifneq (,$(wildcard ./venv/Scripts/python.exe))
PYTHON := $(abspath ./venv/Scripts/python.exe)
endif
else
ifneq (,$(wildcard ./venv/bin/python))
PYTHON := $(abspath ./venv/bin/python)
endif
endif

instructions:
	@echo "[NOTE]: If you see any errors, make sure your virtual environment is active!"

build: instructions
	$(PYTHON) -m pip install -r requirements.txt


run: instructions
	cd ./src/github_projects_burndown_chart \
	&& $(PYTHON) main.py $(type) $(name) $(opts)

test: instructions
	$(PYTHON) -m coverage run \
		--source=src/github_projects_burndown_chart \
		--branch \
		-m unittest discover -v

.PHONY: build run test