#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

question='import sys, os

package_name = sys.argv[2]
name = sys.argv[3]
version = sys.argv[4]

pkg = None
try:
    pkg = __import__(name)
    if pkg.VERSION != version:
        print("expected {0} VERSION to be {1}, got {2}".format(name, version, pkg.VERSION))
        pkg = None
except ImportError:
    print("Could not import {0}".format(name))
    pkg = None

if not pkg:
    import pip
    pip.main(["install", "-e", os.path.join(sys.argv[1], "tests", package_name)])
'

# Install our fake dependencies
python -c "$question" $DIR "fake_input_algorithms" "input_algorithms" "0.5"
python -c "$question" $DIR "fake_addon1" "fake_addon" "0.1"
python -c "$question" $DIR "fake_addon2" "fake_addon2" "0.1"

# Run the tests
nosetests --with-noy $@
