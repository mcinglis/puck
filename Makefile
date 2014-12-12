

$(shell mkdir -p .make)


.PHONY: all
all:


.PHONY: test
test: tests
	cd tests && ./run.py


.PHONY: tests
tests: .make/tests

.make/tests:
	cd tests && ./setup.bash
	@touch $@


.PHONY: clean-tests
clean-tests:
	rm -rf tests/package{1,2,3,4,5} .make/tests


.PHONY: clean
clean: clean-tests



