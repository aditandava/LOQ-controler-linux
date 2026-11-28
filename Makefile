.PHONY: build check run test clean
build:            ## rebuild src/, loq_controller_install.sh and loq_rgb.sh from the section files
	python3 tools/build.py
check: build      ## build + syntax + shell + unit tests
	python3 tools/check.py
test:
	python3 -m unittest discover -s tests -v
run: build        ## open the GUI straight from the source tree
	python3 src/loq-center
status: build     ## print detected hardware data as JSON
	python3 src/loq-center --status
clean:  
	rm -rf build
