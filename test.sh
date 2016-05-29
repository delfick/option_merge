#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

question='import sys, os
input_algorithms = None
try:
    import input_algorithms
    if input_algorithms.VERSION != "0.5":
        print("expected VERSION to be 0.5")
        input_algorithms = None
except ImportError:
    print("Could not import input_algorithms")
    input_algorithms = None

if not input_algorithms:
    import pip
    pip.main(["install", "-e", os.path.join(sys.argv[1], "tests", "fake_input_algorithms")])
'
python -c "$question" $DIR

nosetests --with-noy $@
