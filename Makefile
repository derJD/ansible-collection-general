AGBIN ?= ansible-galaxy
CDIR ?= /tmp/ansible-collections

.PHONY: all

all: lint package install list

lint:
	ansible-lint --parseable-severity -x experimental
package:
	${AGBIN} collection build --output-path ${CDIR}
install:
	${AGBIN} collection install -f ${CDIR}/*.tar.gz
list:
	${AGBIN} collection list
publish:
	${AGBIN} collection publish -v ${CDIR}/*.tar.gz
clean:
	rm -rfv ${CDIR}