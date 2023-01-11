init: buildpy buildc

PYPACKAGE = pip

buildpy:
	@echo "Installing Python dependencies..."
ifeq ($(PYPACKAGE),pip)
	@echo "Using pip to install dependencies..."
	pip install -r frozen-requirements.txt
else
ifeq ($(PYPACKAGE),conda)
	@echo "Using conda to install dependencies..."
	conda install --yes --file requirements.txt
else
	$(error "ERROR: Unknown Python package manager: $(PYPACKAGE)")
endif
endif

test:
	python -m unittest discover --pattern=test_*.py --verbose

buildc:
	@echo "\nBuilding C code executables..."
	$(MAKE) -C oneflux_steps

.PHONY: init test buildpy buildc
