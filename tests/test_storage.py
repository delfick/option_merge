# coding: spec

from option_merge.converter import Converter, Converters
from option_merge.storage import Storage, DataPath
from option_merge.merge import MergedOptions
from option_merge.not_found import NotFound
from option_merge.path import Path

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
d7 = mock.Mock(name="d7", spec=[])
d8 = mock.Mock(name="d8", spec=[])

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

c1 = mock.Mock(name="c1")
c2 = mock.Mock(name="c2")
c3 = mock.Mock(name="c3")
c4 = mock.Mock(name="c4")
c5 = mock.Mock(name="c5")
c6 = mock.Mock(name="c6")

describe TestCase, "Storage":
    before_each:
        self.storage = Storage()

    it "Has data and deleted paths":
        self.assertEqual(self.storage.deleted, [])
        self.assertEqual(self.storage.data, [])

    it "adds new data at the start":
        path1 = Path(mock.Mock(name="path1"))
        path2 = Path(mock.Mock(name="path2"))

        data1 = mock.Mock(name="data1")
        data2 = mock.Mock(name="data2")

        source1 = mock.Mock(name="source1")
        source2 = mock.Mock(name="source2")

        converter1 = mock.Mock(name="converter1")
        converter2 = mock.Mock(name="converter2")

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
            self.storage.add(Path(["a", "b"]), d1)
            self.storage.add(Path(["b", "c"]), d2)
            self.storage.add(Path(["a", "b"]), d3)
            self.assertEqual(self.storage.data, [(["a", "b"], d3, None), (["b", "c"], d2, None), (["a", "b"], d1, None)])
            self.storage.delete("a.b")
            self.assertEqual(self.storage.data, [(["b", "c"], d2, None), (["a", "b"], d1, None)])

        it "removes first thing starting with the same path":
            self.storage.add(Path(["a", "b", "c"]), d1)
            self.storage.add(Path(["b", "c"]), d2)
            self.storage.add(Path(["a", "b", "d"]), d3)
            self.storage.add(Path(["a", "bd"]), d4)
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["a", "b", "d"], d3, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])
            self.storage.delete("a.b")
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])

            self.storage.delete("a.b")
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["b", "c"], d2, None)])

        it "deletes inside the info if it can":
            self.storage.add(Path(["a", "b", "c"]), d1)
            self.storage.add(Path(["b", "c"]), d2)
            self.storage.add(Path(["a", "b"]), d3)
            self.storage.add(Path(["a", "bd"]), d4)
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
            self.storage.add(Path(["a", "b", "c"]), d1)
            self.storage.add(Path(["b", "c"]), d2)
            self.storage.add(Path(["a", "b", "d"]), d3)
            self.storage.add(Path(["a", "bd"]), d4)
            self.assertEqual(self.storage.data, [(["a", "bd"], d4, None), (["a", "b", "d"], d3, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])

            with self.fuzzyAssertRaisesError(KeyError, "a.c"):
                self.storage.delete("a.c")

        it "works with empty path":
            self.storage.add(Path([]), {"a": "b"})
            self.storage.add(Path([]), {"c": "d"})
            self.storage.add(Path([]), {"a": {"d": "e"}})
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

    describe "Getting path and val":
        describe "Same path as info_path":
            it "returns data as is with info_path as the full_path":
                path = Path("a.bd.1")
                info_path = ["a", "bd", "1"]
                data = mock.Mock(name="data")
                source = mock.Mock(name="source")

                self.assertEqual(
                      list(self.storage.determine_path_and_val(path, info_path, data, source))
                    , [(info_path, "", data)]
                    )

        describe "No info_path":
            it "returns value into data":
                val = mock.Mock(name="val")
                data = {'a': {'b': val}}
                path = Path(["a", "b"])
                info_path = []
                source = mock.Mock(name="source")

                self.assertEqual(
                      list(self.storage.determine_path_and_val(path, info_path, data, source))
                    , [(["a", Path("b")], "a.b", val)]
                    )

            it "yields nothing if path not in data":
                val = mock.Mock(name="val")
                data = {'e': {'b': val}}
                path = Path(["a", "b"])
                info_path = []
                source = mock.Mock(name="source")

                self.assertEqual(
                      list(self.storage.determine_path_and_val(path, info_path, data, source))
                    , []
                    )

        describe "Path begins with info_path":
            it "returns found val or dict in the data from path remainder after info_path":
                val = mock.Mock(name="val")
                data = {'b': {'c': {'d': val}}, 'e': 1, 'f':2}
                info_path = Path("a")
                path = Path("a.b")
                source = mock.Mock(name="source")

                self.assertEqual(
                      list(self.storage.determine_path_and_val(path, info_path, data, source))
                      , [(["a", "b"], "b", {"c": {"d": val}})]
                    )

            it "yields nothing if rest of path not in data":
                val = mock.Mock(name="val")
                data = {'e': {'c': {'d': val}}, 'f': 1, 'g':2}
                info_path = Path("a")
                path = Path("a.b")
                source = mock.Mock(name="source")

                self.assertEqual(
                      list(self.storage.determine_path_and_val(path, info_path, data, source))
                      , []
                    )

        describe "Info_path begins with path":
            it "returns made dictionary with remainder info_path":
                data = mock.Mock(name="data")
                info_path = ['a', 'b.e', 'c', 'd']
                path = Path('a.b.e')
                source = mock.Mock(name="source")

                self.assertEqual(
                      list(self.storage.determine_path_and_val(path, info_path, data, source))
                    , [(["a", "b.e"], "", {"c": {"d": data}})]
                    )

    describe "Getting info":
        it "returns all the values it finds":
            self.storage.add(Path(["a", "b", "c"]), d1, source=s1)
            self.storage.add(Path(["b", "c"]), d2, source=s5)
            self.storage.add(Path(["a", "b", "d"]), d3, source=s4)
            self.storage.add(Path(["a", "bd"]), {"1": d4}, source=s2)
            self.storage.add(Path([]), {"a": {"bd": d4}}, source=s1)
            self.storage.add(Path(["a", "b", "c", "d", "e"]), d5, source=s5)
            self.storage.add(Path(["a", "b", "c"]), {"d": {"e": d6}}, source=s6)

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

            path1 = Path("a.bd")
            path2 = Path("a.b.c")
            path3 = Path("a.bd.1")
            path4 = Path("")

            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info(path1)), [(Path("a.bd"), d4, s1), (Path("a.bd"), {"1": d4}, s2)])
            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info(path2)), [(["a", "b", "c"], {"d": {"e": d6}}, s6), (["a", "b", "c"], {'d': {'e': d5}}, s5), (["a", "b", "c"], d1, s1)])
            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info(path3)), [(["a", "bd", "1"], d4, s2)])
            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info(path4))
               , [ (Path(""), {"a": {"b": {"c": {"d": {"e": d6}}}}}, s6)
                 , (Path(""), {"a": {"b": {"c": {"d": {"e": d5}}}}}, s5)
                 , (Path(""), {"a": {"bd": d4}}, s1)
                 , (Path(""), {"a": {"bd": {"1": d4}}}, s2)
                 , (Path(""), {"a": {"b": {"d": d3}}}, s4)
                 , (Path(""), {"b": {"c": d2}}, s5)
                 , (Path(""), {"a": {"b": {"c": d1}}}, s1)
                 ]
               )

        it "returns DataPath objects if that's what it finds":
            self.storage.add(Path(["a", "b", "c"]), d1, source=s1)
            self.storage.add(Path(["b", "c"]), d2, source=s2)
            self.storage.add(Path(["a", "b", "d"]), d3, source=s3)
            self.storage.add(Path(["a", "bd"]), {"1": d4}, source=s4)
            self.assertEqual(self.storage.data, [(["a", "bd"], {"1":d4}, s4), (["a", "b", "d",], d3, s3), (["b", "c"], d2, s2), (["a", "b","c"], d1, s1)])

            self.assertEqual(list((p.path, p.data, p.source()) for p in self.storage.get_info("a")), [(Path(["a"]), {"bd": {"1": d4}}, s4), (Path(["a"]), {'b': {'d': d3}}, s3), (Path(["a"]), {'b': {'c': d1}}, s1)])

        it "raises KeyError if no key is found":
            self.storage.add(Path(["a", "b", "c"]), d1)
            self.storage.add(Path(["b", "c"]), d2)
            self.storage.add(Path(["a", "b", "d"]), d3)
            self.storage.add(Path(["a", "bd"]), {"1": d4})
            self.assertEqual(self.storage.data, [(["a", "bd"], {"1":d4}, None), (["a", "b", "d"], d3, None), (["b", "c"], d2, None), (["a", "b", "c"], d1, None)])

            with self.fuzzyAssertRaisesError(KeyError, "e.g"):
                list(self.storage.get_info("e.g"))

    describe "get":
        it "returns data from the first info":
            data = mock.Mock(name="data")
            path = Path(mock.Mock(name="path"))

            info = mock.Mock(name="info", spec=["data"])
            info2 = mock.Mock(name="info2", spec=["data"])
            info.data = data

            get_info = mock.Mock(name="get_info")
            get_info.return_value = [info, info2]

            with mock.patch.object(self.storage, "get_info", get_info):
                self.assertIs(self.storage.get(path), data)

            get_info.assert_called_once_with(path)

        it "raises KeyError if no info for that key":
            path = Path
            (mock.Mock(name="path"))
            get_info = mock.Mock(name="get_info")
            get_info.return_value = []

            with self.fuzzyAssertRaisesError(KeyError, str(path)):
                with mock.patch.object(self.storage, "get_info", get_info):
                    self.storage.get(path)

            get_info.assert_called_once_with(path)

    describe "Getting source":
        it "returns all sources that contain the provided path":
            self.storage.add(Path(["a", "b", "c"]), d1, source=s1)
            self.storage.add(Path(["b", "c"]), d2, source=s5)
            self.storage.add(Path(["a", "b", "d"]), d3, source=s4)
            self.storage.add(Path(["a", "bd"]), {"1": d4}, source=s2)
            self.storage.add(Path([]), {"a": {"bd": d4}}, source=s1)
            self.storage.add(Path(["a", "b", "c", "d", "e"]), d5, source=s5)
            self.storage.add(Path(["a", "b", "c"]), {"d": {"e": d6}}, source=s6)
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

            self.assertEqual(self.storage.source_for(Path("a.b.c")), [s6, s5, s1])
            self.assertEqual(self.storage.source_for(Path("a.b.c.d.e")), [s6, s5])
            self.assertEqual(self.storage.source_for(Path("a.b.c.d")), [s6, s5])
            self.assertEqual(self.storage.source_for(Path("a.bd")), [s1, s2])
            self.assertEqual(self.storage.source_for(Path("a.bd.1")), [s2])

    describe "keys_after":
        it "yields combined keys from datas":
            self.storage.add(Path([]), {"a": 1, "b": 2})
            self.storage.add(Path([]), {"b": 3, "d": 4})
            self.assertEqual(sorted(self.storage.keys_after("")), sorted(["a", "b", "d"]))

        it "yields from incomplete paths":
            self.storage.add(Path(["1", "2", "3"]), {"a": 1, "b": 2})
            self.assertEqual(sorted(self.storage.keys_after("1")), sorted(["2"]))

        it "stops after complete paths":
            self.storage.add(Path(["1", "2", "3"]), {"a": 1, "b": 2})
            self.storage.add(Path(["1"]), d1)
            self.assertEqual(sorted(self.storage.keys_after("1")), sorted([]))

    describe "as_dict":
        it "Returns the dictionary if there is only one":
            self.storage.add(Path([]), {"a": 1, "b": 2})
            self.assertEqual(self.storage.as_dict(Path([])), {"a": 1, "b": 2})

        it "merges from the back to the front if there is multiple dictionaries":
            self.storage.add(Path([]), {"a": 1, "b": 2})
            self.storage.add(Path([]), {"a": 2, "c": 3})
            self.assertEqual(self.storage.as_dict(Path([])), {"a": 2, "b": 2, "c": 3})

        it "returns the subpath that is provided":
            self.storage.add(Path([]), {"a": {"d": 1}, "b": 2})
            self.storage.add(Path([]), {"a": {"d": 3}, "c": 3})
            self.assertEqual(self.storage.as_dict(Path(["a"])), {"d": 3})

        it "returns subpath if the data is in storage with a prefix":
            self.storage.add(Path([]), {"a": {"d": 1}, "b": 2})
            self.storage.add(Path(["a"]), {"d": 3})
            self.assertEqual(self.storage.as_dict(Path(["a"])), {"d": 3})

        it "unrolls MergedOptions it finds":
            options = MergedOptions.using({"f": 5})
            self.storage.add(Path([]), {"a": {"d": 1}, "b": 2})
            self.storage.add(Path(["a"]), {"d": 3, "e": options})
            self.assertEqual(self.storage.as_dict(Path(["a"])), {"d": 3, "e": {"f": 5}})

        it "ignores unrelated dataz":
            options = MergedOptions.using({"f": 5})
            self.storage.add(Path([]), {"g": {"d": 1}, "b": 2})
            self.storage.add(Path(["a"]), {"d": 3, "e": options})
            self.assertEqual(self.storage.as_dict(Path(["a"])), {"d": 3, "e": {"f": 5}})

        it "doesn't infinitely recurse":
            self.storage.add(Path([]), {"a": {"d": 1}, "b": MergedOptions(storage=self.storage)})
            self.storage.add(Path(["a"]), {"d": 3, "e": MergedOptions(storage=self.storage)})
            self.assertEqual(self.storage.as_dict(Path(["a"])), {"d": 3, "e": {"a": {"e": {}, "d": 3}, "b": {}}})

        it "allows different parts of the same storage":
            self.storage.add(Path([]), {"a": {"d": 1}, "b": 2})
            self.storage.add(Path(["a"]), {"d": 3, "e": MergedOptions(storage=self.storage)})
            self.assertEqual(self.storage.as_dict(Path(["a"])), {"d": 3, "e": {"a": {"e": {}, "d":3}, "b": 2}})

        it "works if the first item is a MergedOptions":
            options = MergedOptions.using({"blah": {"stuff": 1}})
            options.update({"blah": {"stuff": 4, "meh": {"8": "9"}}})
            options["blah"].update({"stuff": {"tree": 20}})
            self.storage.add(Path([]), options)

            self.assertEqual(self.storage.as_dict(Path(["blah", "stuff"])), {"tree": 20})
            self.assertEqual(self.storage.as_dict(Path(["blah", "meh"])), {"8": "9"})

        it "works if the data is prefixed":
            options = MergedOptions()
            options[["blah", "stuff"]] = 1
            self.assertEqual(options.as_dict(), {"blah": {"stuff": 1}})

describe TestCase, "DataPath":
    it "takes in path, data and source":
        p1 = mock.Mock(name="p1")
        path = Path(p1)
        data = mock.Mock(name="data")
        source = mock.Mock(name="source")
        instance = DataPath(path, data, source)
        self.assertIs(instance.path, path)
        self.assertIs(instance.data, data)
        self.assertIs(instance.source, source)

    describe "keys_after":
        it "returns keys from data if path matches":
            p = DataPath(Path(["1", "2"]), {"a":3, "b":4}, s1)
            self.assertEqual(sorted(p.keys_after(Path("1.2"))), sorted(["a", "b"]))

            p = DataPath(Path(["1"]), {"a":3, "b":4}, s1)
            self.assertEqual(sorted(p.keys_after(Path("1"))), sorted(["a", "b"]))

            p = DataPath(Path([]), {"a": {1:2}})
            self.assertEqual(sorted(p.keys_after(Path("a"))), sorted([1]))

        it "raises NotFound if no match":
            p = DataPath(Path(["1", "2"]), {"a":3, "b":4}, s1)
            with self.fuzzyAssertRaisesError(NotFound):
                self.assertEqual(sorted(p.keys_after(Path("1.3"))), sorted([]))

            with self.fuzzyAssertRaisesError(NotFound):
                self.assertEqual(sorted(p.keys_after(Path("3"))), sorted([]))

        it "returns first key after part if path is bigger":
            p = DataPath(Path(["1", "2", "3"]), {"a":3, "b":4}, s1)
            self.assertEqual(sorted(p.keys_after(Path("1"))), sorted(["2"]))

        it "raises NotFound if ask for a bigger path than exists":
            p = DataPath(Path(["1", "2", "3"]), {"a":3, "b":4}, s1)
            with self.fuzzyAssertRaisesError(NotFound):
               sorted(p.keys_after(Path("1.2.3.4")))

    describe "value_after":
        it "returns value":
            p = DataPath(Path(["a"]), d1, s1)
            self.assertIs(p.value_after(Path("a")), d1)

            p = DataPath(Path([]), {"a": d1}, s1)
            self.assertIs(p.value_after(Path("a")), d1)

        it "makes dicts from incomplete paths":
            p = DataPath(Path(["a", "b", "c"]), d1, s1)
            self.assertEqual(p.value_after(Path("a")), {"b": {"c": d1}})

            p = DataPath(Path(["a", "b"]), {"c": d1}, s1)
            self.assertEqual(p.value_after(Path("a")), {"b": {"c": d1}})

        it "raises NotFound if not found":
            p = DataPath(Path(["a", "b", "c"]), d1, s1)
            with self.fuzzyAssertRaisesError(NotFound):
                self.assertEqual(p.value_after(Path("b")), None)

            p = DataPath(Path(["a"]), {"b": d1}, s1)
            with self.fuzzyAssertRaisesError(NotFound):
                p.value_after(Path("a.c"))

            p = DataPath(Path(["1", "2", "3"]), {"a":3, "b":4}, s1)
            with self.fuzzyAssertRaisesError(NotFound):
               p.value_after(Path("1.2.3.4"))

