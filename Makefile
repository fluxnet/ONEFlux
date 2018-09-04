init: buildpy buildc

buildpy:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

test:
	python -m unittest discover --pattern=test_*.py --verbose

buildc:
	@echo "\nBuilding C code executables..."
	$(MAKE) -C oneflux_steps

.PHONY: init test buildpy buildc
