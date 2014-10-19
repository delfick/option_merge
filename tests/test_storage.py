# coding: spec

from option_merge.storage import Storage, Path, Path
from option_merge.helper import NotFound

from noseOfYeti.tokeniser.support import noy_sup_setUp
from delfick_error import DelfickErrorTestMixin
import unittest
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

d1 = mock.Mock(name="d1", spec=[])
d2 = mock.Mock(name="d2", spec=[])
d3 = mock.Mock(name="d3", spec=[])
d4 = mock.Mock(name="d4", spec=[])
d5 = mock.Mock(name="d5", spec=[])
d6 = mock.Mock(name="d6", spec=[])

p1 = mock.Mock(name="p1")
p2 = mock.Mock(name="p2")
p3 = mock.Mock(name="p3")
p4 = mock.Mock(name="p4")
p5 = mock.Mock(name="p5")
p6 = mock.Mock(name="p6")

s1 = mock.Mock(name="s1")
s2 = mock.Mock(name="s2")
s3 = mock.Mock(name="s3")
s4 = mock.Mock(name="s4")
s5 = mock.Mock(name="s5")
s6 = mock.Mock(name="s6")

describe TestCase, "Storage":
    before_each:
        self.storage = Storage()

    it "Has data and deleted paths":
        self.assertEqual(self.storage.deleted, [])
        self.assertEqual(self.storage.data, [])

    it "adds new data at the start":
        path1 = mock.Mock(name="path1")
        path2 = mock.Mock(name="path2")

        data1 = mock.Mock(name="data1")
        data2 = mock.Mock(name="data2")

        source1 = mock.Mock(name="source1")
        source2 = mock.Mock(name="source2")

        self.assertEqual(self.storage.deleted, [])
        self.assertEqual(self.storage.data, [])

        self.storage.add(path1, data1, source=source1)
        self.assertEqual(self.storage.deleted, [])
        self.assertEqual(self.storage.data, [(path1, data1, source1)])

        self.storage.add(path2, data2, source=source2)
        self.assertEqual(self.storage.deleted, [])
        self.assertEqual(self.storage.data, [(path2, data2, source2), (path1, data1, source1)])

    describe "Deleting":
        it "removes first thing with the same path":
            self.storage.add(["a", "b"], d1)
            self.storage.add(["b", "c"], d2)
            self.storage.add(["a", "b"], d3)
            self.assertEqual(self.storage.data, [(["a", "b"], d3, None), (["b", "c"], d2, None), (["a", "b"], d1, None)])
            self.storage.delete("a.b")
            self.assertEqual(self.storage.data, [(["b", "c"], d2, None), (["a", "b"], d1, None)])

        it "removes first thing starting with the same path":
            self.storage.add(["a", "b", "c"], d1)
            self.storage.add(["b", "c"], d2)
            self.storage.add(["a", "b", "d"], d3)
            self.storage.add(["a", "bd"], d4)
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["a", "b", "d"], d3, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])
            self.storage.delete("a.b")
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])

            self.storage.delete("a.b")
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["b", "c"], d2, None)])

        it "deletes inside the info if it can":
            self.storage.add(["a", "b", "c"], d1)
            self.storage.add(["b", "c"], d2)
            self.storage.add(["a", "b"], d3)
            self.storage.add(["a", "bd"], d4)
            def delete_from_data_func(d, p):
                if d is d1:
                    return True
                elif d is d3:
                    return False
                else:
                    assert False, "Unexpected inputs to delete_from_data: d={0}\tp={1}".format(d, p)
            delete_from_data = mock.Mock(name="delete_from_data")
            delete_from_data.side_effect = delete_from_data_func

            with mock.patch.object(self.storage, "delete_from_data", delete_from_data):
                self.storage.delete("a.b.c.d")

            self.assertEqual(delete_from_data.mock_calls, [mock.call(d3, "c.d"), mock.call(d1, "d")])

        it "raises an Index error if it can't find the key":
            self.storage.add(["a", "b", "c"], d1)
            self.storage.add(["b", "c"], d2)
            self.storage.add(["a", "b", "d"], d3)
            self.storage.add(["a", "bd"], d4)
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["a", "b", "d"], d3, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])

            with self.fuzzyAssertRaisesError(KeyError, "a.c"):
                self.storage.delete("a.c")

        it "works with empty path":
            self.storage.add([], {"a": "b"})
            self.storage.add([], {"c": "d"})
            self.storage.add([], {"a": {"d": "e"}})
            self.assertEqual(self.storage.data, [([], {"a": {"d": "e"}}, None), ([], {"c": "d"}, None), ([], {"a": "b"}, None)])

            self.storage.delete("a.d")
            self.assertEqual(self.storage.data, [([], {"a": {}}, None), ([], {"c": "d"}, None), ([], {"a": "b"}, None)])

            self.storage.delete("a")
            self.assertEqual(self.storage.data, [([], {}, None), ([], {"c": "d"}, None), ([], {"a": "b"}, None)])

            self.storage.delete("a")
            self.assertEqual(self.storage.data, [([], {}, None), ([], {"c": "d"}, None), ([], {}, None)])

    describe "Delete from data":
        it "returns False if the data is not a dictionary":
            for data in (0, 1, True, False, None, [], [1], mock.Mock(name="object"), lambda: 1):
                assert not self.storage.delete_from_data(data, "one.blah")

        it "returns False if the data is a dictionary without desired key":
            for data in ({}, {1:2}, {"two": 2}):
                assert not self.storage.delete_from_data(data, "one.blah")

        it "deletes the item and returns True if the data contains the key":
            data = {"one": 1, "two": 2, "three.four": 3}
            res = self.storage.delete_from_data(data, "one")
            self.assertEqual(data, {"two": 2, "three.four": 3})
            assert res is True

            res = self.storage.delete_from_data(data, "three.four")
            self.assertEqual(data, {"two": 2})
            assert res is True

        it "says false if given an empty string to delete":
            data = {"one": 1, "two": 2, "three.four": 3}
            res = self.storage.delete_from_data(data, "")
            self.assertEqual(data, {"one": 1, "two": 2, "three.four": 3})
            assert res is False

        it "deletes full keys before sub keys":
            data = {"one": 1, "two": 2, "three.four": 3, "three": {"four": 5}}
            res = self.storage.delete_from_data(data, "three.four")
            self.assertEqual(data, {"one": 1, "two": 2, "three": {"four": 5}})
            assert res is True

        it "deletes into dictionaries":
            data = {"one": {"two": {"three.four": {"five": 6}, "seven": 7}}}
            res = self.storage.delete_from_data(data, "one.two.three.four.five")
            self.assertEqual(data, {"one": {"two": {"three.four": {}, "seven": 7}}})
            assert res is True

    describe "Getting info":
        it "returns all the values it finds":
            self.storage.add(["a", "b", "c"], d1, source=s1)
            self.storage.add(["b", "c"], d2, source=s5)
            self.storage.add(["a", "b", "d"], d3, source=s4)
            self.storage.add(["a", "bd"], {"1": d4}, source=s2)
            self.storage.add([], {"a": {"bd": d4}}, source=s1)
            self.storage.add(["a", "b", "c", "d", "e"], d5, source=s5)
            self.storage.add(["a", "b", "c"], {"d": {"e": d6}}, source=s6)
            self.assertEqual(self.storage.data
                , [ (["a", "b", "c"], {"d": {"e": d6}}, s6)
                  , (["a", "b", "c", "d", "e"], d5, s5)
                  , ([], {"a": {"bd": d4}}, s1)
                  , (["a", "bd"], {"1":d4}, s2)
                  , (["a", "b", "d"], d3, s4)
                  , (["b", "c"], d2, s5)
                  , (["a", "b", "c"], d1, s1)
                  ]
                )

            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info("a.bd")), [(["a", "bd"], d4, s1), (["a", "bd"], {"1": d4}, s2)])
            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info("a.b.c")), [(["a", "b", "c"], {"d": {"e": d6}}, s6), (["a", "b", "c", "d", "e"], d5, s5), (["a", "b", "c"], d1, s1)])
            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info("a.bd.1")), [(["a", "bd", "1"], d4, s2)])

        it "returns Path objects if that's what it finds":
            self.storage.add(["a", "b", "c"], d1, source=s1)
            self.storage.add(["b", "c"], d2, source=s2)
            self.storage.add(["a", "b", "d"], d3, source=s3)
            self.storage.add(["a", "bd"], {"1": d4}, source=s4)
            self.assertEqual(self.storage.data, [(["a", "bd"], {"1":d4}, s4), (["a", "b", "d",], d3, s3), (["b", "c"], d2, s2), (["a", "b","c"], d1, s1)])

            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info("a")), [(["a", "bd"], {"1": d4}, s4), (["a", "b", "d"], d3, s3), (["a", "b", "c"], d1, s1)])

        it "raises KeyError if no key is found":
            self.storage.add(["a", "b", "c"], d1)
            self.storage.add(["b", "c"], d2)
            self.storage.add(["a", "b", "d"], d3)
            self.storage.add(["a", "bd"], {"1": d4})
            self.assertEqual(self.storage.data, [(["a", "bd"], {"1":d4}, None), (["a", "b", "d"], d3, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])

            with self.fuzzyAssertRaisesError(KeyError, "e.g"):
                list(self.storage.get_info("e.g"))

    describe "get":
        it "returns data from the first info":
            data = mock.Mock(name="data")
            path = mock.Mock(name="path")

            info = mock.Mock(name="info", spec=["data"])
            info2 = mock.Mock(name="info2", spec=["data"])
            info.data = data

            get_info = mock.Mock(name="get_info")
            get_info.return_value = [info, info2]

            with mock.patch.object(self.storage, "get_info", get_info):
                self.assertIs(self.storage.get(path), data)

            get_info.assert_called_once_with(path)

        it "raises KeyError if no info for that key":
            path = mock.Mock(name="path")
            get_info = mock.Mock(name="get_info")
            get_info.return_value = []

            with self.fuzzyAssertRaisesError(KeyError, path):
                with mock.patch.object(self.storage, "get_info", get_info):
                    self.storage.get(path)

            get_info.assert_called_once_with(path)

    describe "Getting source":
        it "returns first non dict data source":
            self.storage.add(["a", "b", "c"], d1, source=s1)
            self.storage.add(["b", "c"], d2, source=s5)
            self.storage.add(["a", "b", "d"], d3, source=s4)
            self.storage.add(["a", "bd"], {"1": d4}, source=s2)
            self.storage.add([], {"a": {"bd": d4}}, source=s1)
            self.storage.add(["a", "b", "c", "d", "e"], d5, source=s5)
            self.storage.add(["a", "b", "c"], {"d": {"e": d6}}, source=s6)
            self.assertEqual(self.storage.data
                , [ (["a", "b", "c"], {"d": {"e": d6}}, s6)
                  , (["a", "b", "c", "d", "e"], d5, s5)
                  , ([], {"a": {"bd": d4}}, s1)
                  , (["a", "bd"], {"1":d4}, s2)
                  , (["a", "b", "d"], d3, s4)
                  , (["b", "c"], d2, s5)
                  , (["a", "b", "c"], d1, s1)
                  ]
                )

            self.assertEqual(self.storage.source_for("a.b.c"), [s1])
            self.assertEqual(self.storage.source_for("a.b.c.d.e"), [s6])
            self.assertEqual(self.storage.source_for("a.b.c.d"), [s6, s5])
            self.assertEqual(self.storage.source_for("a.bd"), [s1])
            self.assertEqual(self.storage.source_for("a.bd.1"), [s2])

    describe "keys_after":
        it "yields combined keys from datas":
            self.storage.add([], {"a": 1, "b": 2})
            self.storage.add([], {"b": 3, "d": 4})
            self.assertEqual(sorted(self.storage.keys_after("")), sorted(["a", "b", "d"]))

        it "yields from incomplete paths":
            self.storage.add(["1", "2", "3"], {"a": 1, "b": 2})
            self.assertEqual(sorted(self.storage.keys_after("1")), sorted(["2"]))

        it "stops after complete paths":
            self.storage.add(["1", "2", "3"], {"a": 1, "b": 2})
            self.storage.add(["1"], d1)
            self.assertEqual(sorted(self.storage.keys_after("1")), sorted([]))

describe TestCase, "Path":
    it "takes in path, data and source":
        path = mock.Mock(name="path")
        data = mock.Mock(name="data")
        source = mock.Mock(name="source")
        instance = Path(path, data, source)
        self.assertIs(instance.path, path)
        self.assertIs(instance.data, data)
        self.assertIs(instance.source, source)

    describe "keys_after":
        it "returns keys from data if path matches":
            p = Path(["1", "2"], {"a":3, "b":4}, s1)
            self.assertEqual(sorted(p.keys_after("1.2")), sorted(["a", "b"]))

        it "raises NotFound if no match":
            p = Path(["1", "2"], {"a":3, "b":4}, s1)
            with self.fuzzyAssertRaisesError(NotFound):
                self.assertEqual(sorted(p.keys_after("1.3")), sorted([]))

            with self.fuzzyAssertRaisesError(NotFound):
                self.assertEqual(sorted(p.keys_after("3")), sorted([]))

        it "returns first key after part if path is bigger":
            p = Path(["1", "2", "3"], {"a":3, "b":4}, s1)
            self.assertEqual(sorted(p.keys_after("1")), sorted(["2"]))

    describe "value_after":
        it "returns value":
            p = Path(["a"], d1, s1)
            self.assertIs(p.value_after("a"), d1)

            p = Path([], {"a": d1}, s1)
            self.assertIs(p.value_after("a"), d1)

        it "makes dicts from incomplete paths":
            p = Path(["a", "b", "c"], d1, s1)
            self.assertEqual(p.value_after("a"), {"b": {"c": d1}})

            p = Path(["a", "b"], {"c": d1}, s1)
            self.assertEqual(p.value_after("a"), {"b": {"c": d1}})

        it "raises NotFound if not found":
            p = Path(["a", "b", "c"], d1, s1)
            with self.fuzzyAssertRaisesError(NotFound):
                self.assertEqual(p.value_after("b"), None)

            p = Path(["a"], {"b": d1}, s1)
            with self.fuzzyAssertRaisesError(NotFound):
                p.value_after("a.c")

