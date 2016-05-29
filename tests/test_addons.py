# coding: spec

from option_merge.addons import find_input_algorithms

from delfick_error import DelfickErrorTestMixin
import unittest

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "finding input_algorithms":
    it "complains if the package can't be found":
        with self.fuzzyAssertRaisesError(Exception, "To use option_merge addons .+"):
            find_input_algorithms("blah_package")

    it "complains if the package has the wrong version":
        with self.fuzzyAssertRaisesError(Exception, "Have invalid version of input_algorithms\terror=\(input-algorithms 0.5 \(.*/tests/fake_input_algorithms\), Requirement.parse\('input_algorithms==0.1'\)\)"):
            find_input_algorithms(version="==0.1")

