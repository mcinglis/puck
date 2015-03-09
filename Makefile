

.PHONY: all
all:


.PHONY: test
test: tests
	cd tests && ./run.py


.PHONY:
tests: tests/.make
tests/.make:
	cd tests && ./setup.bash
	@touch $@


.PHONY: clean
clean:
	rm -rf tests/package{1,2,3,4,5} tests/.make


