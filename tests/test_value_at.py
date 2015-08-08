# coding: spec

from option_merge.value_at import value_at
from option_merge import MergedOptions
from option_merge import helper as hp
from option_merge.path import Path

import itertools

from delfick_error import DelfickErrorTestMixin
import unittest
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "value_at":
    it "returns as is if no path":
        data = mock.Mock(name="data")
        chain = mock.Mock(name="chain")
        self.assertEqual(value_at(data, None), ([], data))
        self.assertEqual(value_at(data, None, chain=chain), (chain, data))

    it "raises NotFound if no more path left and still at a dictionary":
        with self.fuzzyAssertRaisesError(hp.NotFound):
            value_at({1:2}, "somewhere")

    it "returns data at path if it's in data":
        value = mock.Mock(name="value")
        path = mock.Mock(name="path")
        data = {path: value}
        self.assertEqual(value_at(data, path), (Path(path), value))

        c1 = mock.Mock(name="c1")
        c2 = mock.Mock(name="c2")
        chain = [c1, c2]
        self.assertEqual(value_at(data, path, chain=chain), ([c1, c2, path], value))

    it "does largest matching first":
        value = mock.Mock(name="value")
        value2 = mock.Mock(name="value2")
        value3 = mock.Mock(name="value3")
        data = {"blah": {"meh": value}}
        self.assertEqual(value_at(data, "blah.meh"), (Path(["blah", "meh"]), value))

        data["blah.meh"] = value2
        self.assertEqual(value_at(data, "blah.meh"), (Path("blah.meh"), value2))

        data["blah.meh"] = {"stuff": value3}
        self.assertEqual(value_at(data, "blah.meh.stuff"), (Path(["blah.meh", "stuff"]), value3))

    it "skips misleading paths":
        value = mock.Mock(name="value")
        value2 = mock.Mock(name="value2")
        data = {"blah": {"meh": {"stuff": value}}, "blah.meh": {"tree": 3}}
        self.assertEqual(value_at(data, "blah.meh.stuff"), (["blah", "meh", "stuff"], value))

    it "skips paths with the same storage":
        data = MergedOptions.using({"a": "blah"})
        self.assertEqual(value_at(data, "a"), (Path("a"), "blah"))
        data["a"] = data["a"]
        self.assertEqual(value_at(data, "a"), (Path("a"), "blah"))

