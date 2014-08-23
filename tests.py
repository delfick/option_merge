# coding: spec

from option_merge import (
      MergedOptions, NotFound, BadPrefix
    , ConverterProperty, KeyValuePairsConverter, AttributesConverter
    )

from noseOfYeti.tokeniser.support import noy_sup_setUp
from delfick_error import DelfickErrorTestMixin
import unittest
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "MergedOptions":
    before_each:
        self.merged = MergedOptions()

    it "has prefix, options and overrides":
        prefix = mock.Mock(name="prefix")
        options = mock.Mock(name="options")
        overrides = mock.Mock(name="overrides")
        merged = MergedOptions(prefix=prefix, options=options, overrides=overrides)
        self.assertIs(merged.prefix, prefix)
        self.assertIs(merged.options, options)
        self.assertIs(merged.overrides, overrides)

        merged = MergedOptions()
        self.assertIs(merged.prefix, None)
        self.assertEqual(merged.options, [])
        self.assertEqual(merged.overrides, {})

    @mock.patch("option_merge.deepcopy")
    it "has classmethod for adding options", fake_deepcopy:
        options1 = mock.Mock(name="options1")
        options2 = mock.Mock(name="options2")
        copy1 = mock.Mock(name="copy1")
        copy2 = mock.Mock(name="copy2")

        def mapper(opts):
            if opts is options1: return copy1
            if opts is options2: return copy2
        fake_deepcopy.side_effect = mapper

        merged = MergedOptions.using(options1, options2)
        self.assertEqual(merged.options, [copy2, copy1])
        fake_deepcopy.assert_has_calls([mock.call(options1), mock.call(options2)])

    describe "Adding more options":

        @mock.patch("option_merge.deepcopy")
        it "has method for adding more options", fake_deepcopy:
            options1 = mock.Mock(name="options1")
            options2 = mock.Mock(name="options2")
            copy1 = mock.Mock(name="copy1")
            copy2 = mock.Mock(name="copy2")

            def mapper(opts):
                if opts is options1: return copy1
                if opts is options2: return copy2
            fake_deepcopy.side_effect = mapper

            merged = MergedOptions()
            merged.update(options1)
            self.assertEqual(merged.options, [copy1])
            fake_deepcopy.assert_has_calls(mock.call(options1))

            merged.update(options2)
            self.assertEqual(merged.options, [copy2, copy1])
            fake_deepcopy.assert_has_calls(mock.call(options2))

        it "Works when there is a prefix":
            options = MergedOptions.using({"a": {"b": 1, "c": 2}})
            a_opt = options["a"]
            self.assertEqual(sorted(a_opt.items()), sorted([("b", 1), ("c", 2)]))

            a_opt.update({"c": 3})
            self.assertEqual(a_opt["c"], 3)

    describe "Getting an item":
        it "raises a KeyError if the key doesn't exist":
            with self.fuzzyAssertRaisesError(KeyError, 'blah'):
                self.merged['blah']

        it "gets the first value for that key if it exists":
            val1 = mock.Mock(name="val1")
            val2 = mock.Mock(name="val2")
            fake_values_for = mock.Mock(name="values_for")
            fake_values_for.return_value = [val1, val2]
            with mock.patch.object(self.merged, 'values_for', fake_values_for):
                self.assertIs(self.merged['blah'], val1)
            fake_values_for.assert_called_once_with('blah')

    describe "Setting an item":
        it "puts it in the overrides dictionary":
            self.assertEqual(self.merged.overrides, {})
            self.merged['blah'] = {}
            self.assertEqual(self.merged.overrides, {'blah':{}})

            self.merged["tree"] = 4
            self.assertEqual(self.merged.overrides, {'blah':{}, "tree": 4})

            self.merged["blah"]["meh"] = "things"
            self.assertEqual(self.merged.overrides, {'blah': {'meh': "things"}, "tree": 4})

            self.merged["blah"] = {"meh": {'r':20}}
            self.merged["blah"]["meh"]["gh"] = 3
            self.assertEqual(self.merged.overrides, {"blah": {"meh": {"gh": 3, 'r':20}}, "tree": 4})

        it "creates missing dictionaries if a prefix doesn't exist":
            self.assertEqual(self.merged.overrides, {})
            self.merged["blah.meh.gh"] = 3
            self.assertEqual(self.merged.overrides, {"blah": {"meh": {"gh": 3}}})

            self.merged["blah.meh.tree"] = 4
            self.assertEqual(self.merged.overrides, {"blah": {"meh": {"gh": 3, "tree": 4}}})

            self.merged["blah.hmm.tree"] = 5
            self.assertEqual(self.merged.overrides, {"blah": {"meh": {"gh": 3, "tree": 4}, "hmm": {"tree": 5}}})

    describe "Deleting an item":
        it "only deletes once":
            self.merged.update({'a':1})
            self.merged.update({'a':2})
            self.merged['a'] = 3
            self.assertEqual(self.merged['a'], 3)

            del self.merged['a']
            self.assertEqual(self.merged['a'], 2)

            del self.merged['a']
            self.assertEqual(self.merged['a'], 1)

        it "complains if there is nothing to delete":
            self.merged['a'] = 3
            self.assertEqual(self.merged['a'], 3)

            del self.merged['a']
            with self.fuzzyAssertRaisesError(KeyError, "a"):
                self.merged['a']
            with self.fuzzyAssertRaisesError(KeyError, "a"):
                del self.merged['a']

            self.merged.update({'b':1})
            self.assertEqual(self.merged['b'], 1)
            del self.merged['b']
            with self.fuzzyAssertRaisesError(KeyError, "b"):
                del self.merged['b']

        it "can delete from a nested dict":
            self.merged.update({'a':1, 'b':{'c':5}})
            self.merged.update({'a':{'c':4}, 'b':{'c':6, 'd':8}})
            self.merged['a'] = {'c':5}

            values = list(self.merged.values_for('b'))
            self.assertEqual(values, [{'c':6, 'd':8}, {'c':5}])

            del self.merged['b']['c']
            values = list(self.merged.values_for('b'))
            self.assertEqual(values, [{'d':8}, {'c':5}])

            del self.merged['b']['c']
            values = list(self.merged.values_for('b'))
            self.assertEqual(values, [{'d':8}])

        it "can delete dot seperated values":
            self.merged.update({'a':1, 'b':{'c':5}})
            self.merged.update({'a':{'c':4}, 'b':{'c':6, 'd':8}})
            self.merged['a'] = {'c':5}

            values = list(self.merged.values_for('b'))
            self.assertEqual(values, [{'c':6, 'd':8}, {'c':5}])

            del self.merged['b.c']
            values = list(self.merged.values_for('b'))
            self.assertEqual(values, [{'d':8}, {'c':5}])

            del self.merged['b.c']
            values = list(self.merged.values_for('b'))
            self.assertEqual(values, [{'d':8}])

    describe "Getting all values for a key":
        it "finds all the values":
            self.merged.update({'a':1, 'b':{'c':5}})
            self.merged.update({'a':{'c':4}, 'b':4})
            self.merged['a'] = {'c':5}
            values = list(self.merged.values_for('a'))
            self.assertEqual(values, [{'c':5}, {'c':4}, 1])

            self.merged['a'] = 400
            values = list(self.merged.values_for('a'))
            self.assertEqual(values, [400, {'c':4}, 1])

    describe "Clean prefix":
        it "deletes a prefix if it is an empty dictionary":
            options = {"blah": {"meh": {}}}
            self.merged.prefix = ["blah", "meh"]
            self.merged.clean_prefix(options)
            self.assertEqual(options, {"blah": {}})

        it "does nothing if prefix is not an empty dictionary":
            options = {}
            self.merged.prefix = ["blah", "meh"]

            self.merged.clean_prefix(options)
            self.assertEqual(options, {})

            options["blah"] = {}
            self.merged.clean_prefix(options)
            self.assertEqual(options, {"blah": {}})

            options["blah"] = {"meh": {1:2}}
            self.merged.clean_prefix(options)
            self.assertEqual(options, {"blah": {"meh": {1:2}}})

    describe "Prefixes":
        describe "Joining key with the prefix":
            it "returns dot prefixed string with just the key if no prefix":
                self.assertEqual(self.merged.prefix_key('blah'), 'blah')

            it "returns dot prefixed string with key after existing prefix":
                self.merged.prefix = ['one', 'two']
                self.assertEqual(self.merged.prefix_key('blah'), 'one.two.blah')

            it "returns without leading dot if no path":
                self.merged.prefix = ['one']
                self.assertEqual(self.merged.prefix_key(''), 'one')

                self.merged.prefix = ['one', 'two']
                self.assertEqual(self.merged.prefix_key(''), 'one.two')

        describe "Making new MergedOptions":
            it "uses same options and overrides":
                prefix = mock.Mock(name="prefix")
                options = mock.Mock(name="options")
                overrides = mock.Mock(name="overrides")
                self.merged.options = options
                self.merged.overrides = overrides
                prefixed = self.merged.prefixed(prefix)
                self.assertIs(prefixed.prefix, prefix)
                self.assertIs(prefixed.options, options)
                self.assertIs(prefixed.overrides, overrides)

        describe "Getting value at some prefix":
            it "returns options as is if no prefix":
                opts = mock.Mock(name="opts")
                self.assertIs(self.merged.after_prefix(opts), opts)

                self.assertIs(self.merged.after_prefix(opts, prefix=None), opts)

                self.merged.prefix = ["blah"]
                self.assertIs(self.merged.after_prefix(opts, prefix=None), opts)

            it "uses prefix on merged if none specified":
                opts = {"blah": {"meh": 3}}
                self.merged.prefix = ["blah"]
                self.assertEqual(self.merged.after_prefix(opts), {"meh": 3})

            it "uses specified prefix if specified":
                opts = {"blah": {"meh": {4:5}}}
                self.merged.prefix = ["blah"]
                self.assertEqual(self.merged.after_prefix(opts, prefix="blah.meh"), {4:5})

            it "complains if prefix is a value":
                opts = {"blah": {"meh": 3}}
                self.merged.prefix = ["blah"]
                with self.fuzzyAssertRaisesError(BadPrefix, "Value is not a dictionary", key="blah.meh", found=int):
                    self.merged.after_prefix(opts, prefix="blah.meh")

            it "returns empty dictionary instead of complaining if told to be silent":
                opts = {}
                self.merged.prefix = ["blah"]
                self.assertEqual(self.merged.after_prefix(opts, prefix="blah.meh", silent=True), {})
                self.assertEqual(opts, {})

            it "creates empty dictionaries if silent and create":
                opts = {}
                self.merged.prefix = ["blah"]
                self.assertEqual(self.merged.after_prefix(opts, prefix="blah.meh", silent=True, create=True), {})
                self.assertEqual(opts, {"blah": {"meh": {}}})

        describe "Getting value or NotFound from some dot seperated string":
            it "returns options as is if no path":
                opts = mock.Mock(name="opts")
                self.assertIs(self.merged.at_path(None, opts), opts)
                self.assertIs(self.merged.at_path([], opts), opts)
                self.assertIs(self.merged.at_path("", opts), opts)

            it "raises KeyError if can't prefix doesn't exist or isn't a dictionary":
                with self.fuzzyAssertRaisesError(KeyError, "blah"):
                    self.assertIs(self.merged.at_path("blah.meh", {}), NotFound)
                with self.fuzzyAssertRaisesError(BadPrefix, "Value is not a dictionary", key="blah", found=int):
                    self.assertIs(self.merged.at_path("blah.meh", {"blah": 3}), NotFound)

            it "returns NotFound if found prefix but not the path":
                self.assertIs(self.merged.at_path("blah", {}), NotFound)
                self.assertIs(self.merged.at_path("blah.meh", {"blah": {}}), NotFound)

            it "returns the value at the path if it exists":
                opts = {'a': {'b': {'c':1}, 'd':5}, 't': 6}
                self.assertEqual(self.merged.at_path('a.b', opts), {'c':1})
                self.assertEqual(self.merged.at_path('t', opts), 6)
                self.assertEqual(self.merged.at_path('a.d', opts), 5)

    describe "Getting keys":
        describe "Getting all keys from a dictionary":
            it "returns leaf keys":
                opts = {'a': {'b': {'c':1}, 'd':5}, 't': 6, 'u': {}}
                self.assertEqual(sorted(self.merged.all_keys_from(opts)), sorted(["a.b.c", "a.d", "t"]))

        describe "Getting keys on a mergedOptions":
            it "returns one level of keys":
                self.merged.update({'a': {'b': {'c':1}, 'd':5}, 't': 6, 'u': {}})
                self.assertEqual(sorted(self.merged.keys()), sorted(["a", "t", "u"]))

                self.merged.update({'a': 3, 'e':7})
                self.assertEqual(sorted(self.merged.keys()), sorted(["a", "t", "u", "e"]))

                self.merged['h'] = 10
                self.assertEqual(sorted(self.merged.keys()), sorted(["a", "t", "u", "e", "h"]))

            it "returns one level of keys from prefix":
                prefixed = self.merged.prefixed('a')
                self.merged.update({'a': {'b': {'c':1}, 'd':5}, 't': 6, 'u': {}})
                self.assertEqual(sorted(prefixed.keys()), sorted(["b", "d"]))

                self.merged.update({'a': {'g':6}, 'e':7})
                self.assertEqual(sorted(prefixed.keys()), sorted(["b", "d", "g"]))

                self.merged['a'] = {"h": 9}
                self.assertEqual(sorted(prefixed.keys()), sorted(["b", "d", "g", "h"]))

        describe "Getting all keys":
            it "Gets full keys from everywhere":
                self.merged.update({'a': {'b': {'c':1}, 'd':5}, 't': 6, 'u': {}})
                self.merged.update({'a': {'g':6}, 'e':7})
                self.merged['a'] = {"d":34, "r":9001}
                self.assertEqual(sorted(self.merged.all_keys()), sorted(["a.b.c", "a.d", "t", "a.g", "e", "a.r"]))

    describe "Iteration":
        it "just goes through the keys":
            fake_keys = mock.Mock(name="keys")
            fake_keys.side_effect = lambda: iter([1, 2, 3])
            with mock.patch.object(self.merged, 'keys', fake_keys):
                self.assertEqual(list(self.merged), [1, 2, 3])

    describe "Length":
        it "Counts the number of keys":
            keys = []
            fake_keys = mock.Mock(name="keys")
            fake_keys.side_effect = lambda: iter(keys)
            with mock.patch.object(self.merged, 'keys', fake_keys):
                self.assertEqual(len(self.merged), 0)

                keys.append(1)
                self.assertEqual(len(self.merged), 1)

                keys.extend([2, 3, 4])
                self.assertEqual(len(self.merged), 4)

    describe "Getting items":
        it "combines everything into one key,value list":
            self.merged.update({'a':1, 'b':{'c':9}})
            self.merged.update({'a':{'c':4}, 'b':4})
            self.merged['a'] = {'c':5, "d":8}
            self.assertEqual(self.merged.items(), {"b":4, "a":{"c":5, "d":8}}.items())

            del self.merged['b']
            self.assertEqual(self.merged.items(), {"b":{'c':9}, "a":{"c":5, "d":8}}.items())

            del self.merged['a.c']
            self.assertEqual(self.merged.items(), {"b":{'c':9}, "a":{"c":4, "d":8}}.items())

            self.assertEqual(self.merged.prefixed(["b"]).items(), {'c': 9}.items())

    describe "Getting as a flat dotted key, value list":
        it "combines everything into one flat list of key value tuples":
            self.merged.update({'a':1, 'b':{'c':9}})
            self.merged.update({'a':{'c':4}, 'b':4})
            self.merged['a'] = {'c':5, "d":8}

            self.assertEqual(sorted(self.merged.as_flat()), sorted([("b", 4), ("a.c", 5), ("a.d", 8)]))

            del self.merged['b']
            self.assertEqual(sorted(self.merged.as_flat()), sorted([("b.c", 9), ("a.c", 5), ("a.d", 8)]))

            del self.merged['a.c']
            self.assertEqual(sorted(self.merged.as_flat()), sorted([("b.c", 9), ("a.c", 4), ("a.d", 8)]))

            self.assertEqual(sorted(self.merged.prefixed(["b"]).as_flat()), sorted([("c", 9)]))

describe TestCase, "Converters":
    it "has a KeyValuePairs converter on MergedOptions":
        result = MergedOptions.KeyValuePairs([("one", "two"), ("three.four", "five")])
        self.assertEqual(result, {"one": "two", "three": {"four": "five"}})

    it "has a Attributes converter on MergedOptions":
        obj = type("obj", (object, ), {"one": "two", "two": "three", "four": "five"})
        result = MergedOptions.Attributes(obj, ("one", "four"), lift="global")
        self.assertEqual(result, {"global": {"one": "two", "four": "five"}})

    describe "Property Converter":
        it "takes a converter":
            converter = mock.Mock(name="converter")
            prop = ConverterProperty(converter)
            self.assertIs(prop.converter, converter)

        it "has a __get__ for instantiating the converter and calling convert":
            a = mock.Mock(name="a")
            b = mock.Mock(name="b")
            c = mock.Mock(name="c")
            d = mock.Mock(name="d")
            converted = mock.Mock(name="converted")
            instance = mock.Mock(name="instance")

            converter = mock.Mock(name="converter")
            converter.return_value = instance
            instance.convert.return_value = converted

            prop = ConverterProperty(converter)
            self.assertIs(prop.__get__()(c, d, a=b, b=a), converted)

            converter.assert_called_once_with(c, d, a=b, b=a)
            instance.convert.assert_called_once()

        it "can be used as a property":
            givenresult = mock.Mock(name="givenresult")
            producedresult = mock.Mock(name="producedresult")
            class Converter(object):
                def __init__(self, given):
                    self.given = given

                def convert(self):
                    return (self.given, producedresult)

            class Thing(object):
                myprop = ConverterProperty(Converter)

            self.assertEqual(Thing().myprop(givenresult), (givenresult, producedresult))

    describe "KeyValuePairsConverter":
        it "converts simple key value pairs into a dictionary":
            converter = KeyValuePairsConverter([("one", "two"), (3, 4)])
            self.assertEqual(converter.convert(), {"one": "two", "3": 4})

        it "converts complex key value pairs into a dictionary":
            converter = KeyValuePairsConverter([("one.two", "three"), ("three", "four"), ("five.six.seven", "eight"), ("five.six.nine", "ten")])
            self.assertEqual(converter.convert(), {"one": {"two":"three"}, "three": "four", "five": {"six": {"seven": "eight", "nine": "ten"}}})

        it "Overrides previous keys":
            converter = KeyValuePairsConverter([("one.two", "three"), ("one.two.five", "four")])
            self.assertEqual(converter.convert(), {"one": {"two": {"five": "four"}}})

            # And the other way round
            converter = KeyValuePairsConverter([("one.two.five", "four"), ("one.two", "three")])
            self.assertEqual(converter.convert(), {"one": {"two": "three"}})

    describe "AttributesConverter":
        it "converts all attributes to a dictionary":
            class Obj(object):
                def a(self): pass
                one = "two"

            class Obj2(Obj):
                def b(self): pass
                three = "four"
                _ignored = "because_private"

            obj = Obj2()
            converter = AttributesConverter(obj)
            self.assertEqual(converter.convert(), {"one": "two", "three": "four", "b": obj.b, "a": obj.a})

        it "includes underscored attributes if asked for":
            class Obj(object):
                def a(self): pass
                one = "two"

            class Obj2(Obj):
                def b(self): pass
                three = "four"
                _notignored = "because_private"

            obj = Obj2()
            converter = AttributesConverter(obj, include_underlined=True)
            underlined = [attr for attr in dir(obj) if attr.startswith("_")]

            expected = dict((attr, getattr(obj, attr)) for attr in underlined)
            expected.update({"one": "two", "three": "four", "b": obj.b, "a": obj.a, "_notignored": "because_private"})
            self.assertEqual(converter.convert(), expected)

        it "only includes specified attributes if specified":
            class Obj(object):
                def a(self): pass
                one = None
                blah = "things"
                hi = "hello"

            converter = AttributesConverter(Obj(), ("one", "hi", "__class__"))
            self.assertEqual(converter.convert(), {"one": None, "hi": "hello", "__class__": Obj})

        it "can exclude attributes that have particular values":
            class Obj(object):
                def a(self): pass
                one = None
                blah = "things"
                hi = "hello"

            converter = AttributesConverter(Obj(), ("one", "hi", "__class__"), ignoreable_values=(None, ))
            self.assertEqual(converter.convert(), {"hi": "hello", "__class__": Obj})

        it "can lift the result if provided with a prefix to lift against":
            class Obj(object):
                def a(self): pass
                one = "two"
                blah = "things"
                hi = "hello"

            converter = AttributesConverter(Obj(), ("one", "hi", "__class__"), lift="cats.pandas")
            self.assertEqual(converter.convert(), {"cats": {"pandas": {"one": "two", "hi": "hello", "__class__": Obj}}})

