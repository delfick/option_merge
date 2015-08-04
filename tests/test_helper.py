# coding: spec

from option_merge import MergedOptions
from option_merge import helper as hp
from option_merge.path import Path

import itertools

from noseOfYeti.tokeniser.support import noy_sup_setUp
from delfick_error import DelfickErrorTestMixin
import unittest
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "value_at":
    it "returns as is if no path":
        data = mock.Mock(name="data")
        chain = mock.Mock(name="chain")
        self.assertEqual(hp.value_at(data, None), ([], data))
        self.assertEqual(hp.value_at(data, None, chain=chain), (chain, data))

    it "raises NotFound if no more path left and still at a dictionary":
        with self.fuzzyAssertRaisesError(hp.NotFound):
            hp.value_at({1:2}, "somewhere")

    it "returns data at path if it's in data":
        value = mock.Mock(name="value")
        path = mock.Mock(name="path")
        data = {path: value}
        self.assertEqual(hp.value_at(data, path), (Path(path), value))

        c1 = mock.Mock(name="c1")
        c2 = mock.Mock(name="c2")
        chain = [c1, c2]
        self.assertEqual(hp.value_at(data, path, chain=chain), ([c1, c2, path], value))

    it "does largest matching first":
        value = mock.Mock(name="value")
        value2 = mock.Mock(name="value2")
        value3 = mock.Mock(name="value3")
        data = {"blah": {"meh": value}}
        self.assertEqual(hp.value_at(data, "blah.meh"), (Path(["blah", "meh"]), value))

        data["blah.meh"] = value2
        self.assertEqual(hp.value_at(data, "blah.meh"), (Path("blah.meh"), value2))

        data["blah.meh"] = {"stuff": value3}
        self.assertEqual(hp.value_at(data, "blah.meh.stuff"), (Path(["blah.meh", "stuff"]), value3))

    it "skips misleading paths":
        value = mock.Mock(name="value")
        value2 = mock.Mock(name="value2")
        data = {"blah": {"meh": {"stuff": value}}, "blah.meh": {"tree": 3}}
        self.assertEqual(hp.value_at(data, "blah.meh.stuff"), (["blah", "meh", "stuff"], value))

    it "skips paths with the same storage":
        data = MergedOptions.using({"a": "blah"})
        self.assertEqual(hp.value_at(data, "a"), (Path("a"), "blah"))
        data["a"] = data["a"]
        self.assertEqual(hp.value_at(data, "a"), (Path("a"), "blah"))

describe TestCase, "without_prefix":
    before_each:
        self.path = mock.Mock(name="path", spec=[])

    it "returns path as is if no prefix":
        self.assertIs(hp.without_prefix(self.path), self.path)

    it "returns path as is if no path":
        self.assertIs(hp.without_prefix(None), None)

    it "returns empty string if equals prefix":
        self.assertIs(hp.without_prefix(self.path, prefix=self.path), "")

    it "returns string without prefix if it startswith it":
        self.assertEqual(hp.without_prefix("somewhere.nice.tree", "somewhere.nice"), "tree")

    it "returns path as is if doesn't start with prefix":
        self.assertEqual(hp.without_prefix("somewhere.nicetree", "somewhere.nice"), "somewhere.nicetree")

    it "uses without method if available":
        path = mock.Mock(name="path")
        prefix = mock.Mock(name="prefix")
        new_path = mock.Mock(name="new_path")
        path.without.return_value = new_path
        self.assertIs(hp.without_prefix(path, prefix), new_path)
        path.without.assert_called_once_with(prefix)

describe TestCase, "prefixed_path_list":
    before_each:
        self.path = mock.Mock(name="path")

    it "returns path if no prefix":
        self.assertEqual(hp.prefixed_path_list([Path("1")]), (Path("1"), "1"))

    it "adds prepends prefix":
        p1 = mock.Mock(name="p1")
        p2 = mock.Mock(name="p2")

        self.path.joined.return_value = "path_joined"
        p1.joined.return_value = "p1_joined"
        p2.joined.return_value = "p2.joined"

        self.assertEqual(hp.prefixed_path_list([self.path], [p1, p2]), ([p1, p2, self.path], "{0}.{1}.{2}".format(p1.joined(), p2.joined(), self.path.joined())))

describe TestCase, "prefixed_path_string":
    it "removes superfluous dots":
        for blah in ("blah", ".blah", "blah.", ".blah.", "..blah.", ".blah..", "..blah.."):
            self.assertEqual(hp.prefixed_path_string(blah), ("blah", "blah"))

    it "joins together two paths with one dot":
        blah_possibilities = ["blah", ".blah", "blah.", ".blah.", "blah..", "..blah", "..blah.."]
        stuff_possibilities = [pos.replace("blah", "stuff") for pos in blah_possibilities]

        for pos in blah_possibilities:
            self.assertEqual(hp.prefixed_path_string(pos), ("blah", "blah"))

        for blahpos, stuffpos in (list(itertools.product(blah_possibilities, stuff_possibilities))):
            self.assertEqual(hp.prefixed_path_string(blahpos, prefix=stuffpos), ("stuff.blah", "stuff.blah"))#

describe TestCase, "make_dict":
    it "returns just with first and data if no rest":
        data = mock.Mock(name="data")
        first = mock.Mock(name="first")
        self.assertEqual(hp.make_dict(first, [], data), {first:data})

    it "returns with first and sequence of dicts from rest":
        r1 = mock.Mock(name='r1')
        r2 = mock.Mock(name='r2')
        r3 = mock.Mock(name='r3')
        data = mock.Mock(name="data")
        first = mock.Mock(name="first")
        self.assertEqual(hp.make_dict(first, [r1, r2, r3], data), {first: {r1: {r2: {r3: data}}}})

describe TestCase, "merge_into_dict":
    describe "with normal dictionaries":
        it "merges empty dicts into another empty dict":
            target = {}
            source = {}
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {})

        it "merges a full dict into an empty dict":
            target = {}
            source = {"a":1, "b":2, "c": {"d": 3}}
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"a": 1, "b":2, "c":{"d":3}})

        it "merges a full dict ontop of another full dict":
            target = {"a":5, "b":2, "c": {"e":7}, "f":9}
            hp.merge_into_dict(target, {})
            self.assertEqual(target, {"a":5, "b":2, "c": {"e":7}, "f":9})

            source = {"a":1, "b":2, "c": {"d": 3}}
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"a":1, "b":2, "c": {"d": 3, "e":7}, "f":9})

        it "overrides dictionaries with scalar values":
            target = {"a":5, "b":2, "c": {"e":7}}
            source = {"a":1, "b":2, "c": 3}
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"a":1, "b":2, "c": 3})

        it "overrides scalar values with dictionaries":
            target = {"a":1, "b":2, "c": 3}
            source = {"a":5, "b":2, "c": {"e":7}}
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"a":5, "b":2, "c": {"e": 7}})

    describe "with MergedOptions":
        it "merges a MergedOptions into an empty dictionary":
            target = {}
            source = MergedOptions.using({"a":5, "b":2, "c": {"e":7}})
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"a":5, "b":2, "c": {"e": 7}})

        it "merges a MergedOptions into a full dictionary":
            target = {"a":5, "b":2, "c": {"f":7}}
            source = MergedOptions.using({"a":1, "b":2, "c": {"e":7}})
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"a":1, "b":2, "c": {"f": 7, "e": 7}})

        it "merges a MergedOptions with prefixed data into an empty dictionary":
            target = {"a":5, "b":2, "c": {"f":7}}
            source = MergedOptions()
            source["c"] = {"e": 7}
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"a":5, "b":2, "c": {"f": 7, "e": 7}})

        it "merges a nested MergedOptions into a dictionary":
            source1 = MergedOptions.using({"one": 1, "two": 2, "three": {"four": 4}})
            source2 = MergedOptions.using({"one": "ONE"})
            source3 = MergedOptions.using({"four": "FOUR"})
            source = MergedOptions.using({"a": 1}, source1, {"cap": source2})
            source["three"] = source3

            self.assertEqual(source.as_dict(), {"a":1, "cap":{"one": "ONE"}, "three": {"four": "FOUR"}, "one": 1, "two": 2})

            target = {"one": "thousand", "and": "fifteen"}
            hp.merge_into_dict(target, source)
            self.assertEqual(target, {"and": "fifteen", "a":1, "cap":{"one": "ONE"}, "three": {"four": "FOUR"}, "one": 1, "two": 2})

