# coding: spec

from option_merge.addons import find_input_algorithms
from option_merge.addons import Addon, Result
from option_merge import MergedOptions

from noseOfYeti.tokeniser.support import noy_sup_setUp
from delfick_error import DelfickErrorTestMixin
import unittest

from fake_addon.badresult import NotResult

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "finding input_algorithms":
    it "complains if the package can't be found":
        with self.fuzzyAssertRaisesError(Exception, "To use option_merge addons .+"):
            find_input_algorithms("blah_package")

    it "complains if the package has the wrong version":
        with self.fuzzyAssertRaisesError(Exception, "Have invalid version of input_algorithms\terror=\(input-algorithms 0.5 \(.*/tests/fake_input_algorithms\), Requirement.parse\('input_algorithms==0.1'\)\)"):
            find_input_algorithms(version="==0.1")

describe TestCase, "Addon":
    before_each:
        self.configuration = MergedOptions.using({"one": { "two": "34" } })

    it "complains if can't find an entry_point":
        with self.fuzzyAssertRaisesError(Addon.NoSuchAddon):
            list(Addon.get("nonexisting", self.configuration))

    it "will get result for all matching entry_points":
        results = list(Addon.get("same", self.configuration))
        self.assertEqual(len(results), 2)
        self.assertNotEqual(results[0], results[1])

    it "will complain about entry points it can't import":
        with self.fuzzyAssertRaisesError(Addon.BadImport, "Error whilst resolving entry_point", importing="unimportable", module="fake_addon2.unimportable", error="No module named wasdf"):
            list(Addon.get("unimportable", self.configuration))

    it "will complain about entry points that have no __option_merge__ hook":
        with self.fuzzyAssertRaisesError(Addon.BadImport, "Error after resolving entry_point", importing="nohook", module="fake_addon2.no_hook", error="Didn't find an __option_merge__ function"):
            list(Addon.get("nohook", self.configuration))

    it "will complain about entry_points that don't use the make_result factory":
        with self.fuzzyAssertRaisesError(Addon.BadAddon, "Addon's __option_merge__ returned something wrong!", expected=Result, got=NotResult, addon="badresult"):
            list(Addon.get("badresult", self.configuration))

