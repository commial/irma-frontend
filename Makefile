TESTS=./tests
RESULTS=${TESTS}/results
PACKAGES=frontend
OPTIONS=--cover-erase --with-coverage --cover-package=${PACKAGES} --cover-html --cover-html-dir=${RESULTS} --with-xunit --xunit-file=${RESULTS}/frontend_xunit.xml


test-env:
	mkdir -p ${RESULTS}


test: test-env
	nosetests ${TESTS}


testc: test-env
	pylint ${PACKAGES} 2>&1 > ${RESULTS}/brain.pylint || exit 0
	nosetests ${OPTIONS} ${TESTS}
