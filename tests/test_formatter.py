# coding: spec

from option_merge.formatter import MergedOptionStringFormatter, NotSpecified
from option_merge import MergedOptions

from noseOfYeti.tokeniser.support import noy_sup_setUp
from delfick_error import DelfickErrorTestMixin
import unittest
import string
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "MergedOptionStringFormatter":
    before_each:
        self.all_options = mock.MagicMock(name="all_options")
        self.option_path = mock.Mock(name="option_path")
        self.chain = mock.Mock(name="chain")
        self.value = mock.Mock(name="value")

    it "takes in all_options, option_path, chain and value":
        formatter = MergedOptionStringFormatter(self.all_options, self.option_path, chain=self.chain, value=self.value)
        self.assertIs(formatter.all_options, self.all_options)
        self.assertIs(formatter.option_path, self.option_path)
        self.assertIs(formatter.chain, self.chain)
        self.assertIs(formatter.value, self.value)

    it "defaults chain to a list with option_path in it":
        formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
        self.assertEqual(formatter.chain, [self.option_path])

    it "defaults value to NotSpecified":
        formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
        self.assertIs(formatter.value, NotSpecified)

    describe "format":
        it "returns the value if it's not a string":
            value = mock.Mock(name="value")
            self.assertIs(MergedOptionStringFormatter(self.all_options, self.option_path, value=value).format(), value)

        it "uses get_string if the value isn't specified":
            ret = mock.Mock(name="ret")
            get_string = mock.Mock(name="get_string")
            get_string.return_value = ret

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path, value=NotSpecified)
            with mock.patch.object(formatter, "get_string", get_string):
                self.assertIs(formatter.format(), ret)

            get_string.assert_called_once_with(self.option_path)

        it "calls format on super if the value is a string":
            result = mock.Mock(name="result")
            format_func = mock.Mock(name="format", return_value=result)

            with mock.patch.object(string.Formatter, "format", format_func):
                self.assertIs(MergedOptionStringFormatter(self.all_options, self.option_path, value="asdf").format(), result)

            format_func.assert_called_once_with("asdf")

    describe "with_option_path":
        it "appends value to the chain, sets option_path to the value and sets value to NotSpecified":
            one = MergedOptionStringFormatter(self.all_options, self.option_path, chain=[1], value=2)
            two = one.with_option_path(3)
            self.assertIs(two.all_options, self.all_options)
            self.assertIs(two.option_path, 3)
            self.assertEqual(two.chain, [1, 3])
            self.assertEqual(two.value, NotSpecified)

    describe "get_string":
        it "gets the key from all_options":
            meh = mock.Mock(name="meh")
            blah = mock.Mock(name="blah")
            all_options = {meh: blah}

            self.assertIs(MergedOptionStringFormatter(all_options, self.option_path).get_string(meh), blah)

    describe "get_field":
        it "returns special if special_get_field returns something":
            ret = mock.Mock(name="ret")
            special_get_field = mock.Mock(name="special_get_field")
            special_get_field.return_value = ret

            args = mock.Mock(name="args")
            value = mock.Mock(name="value")
            kwargs = mock.Mock(name="kwargs")
            format_spec = mock.Mock(name="format_spec")

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
            with mock.patch.object(formatter, "special_get_field", special_get_field):
                self.assertIs(formatter.get_field(value, args, kwargs, format_spec=format_spec), ret)

            special_get_field.assert_called_once_with(value, args, kwargs, format_spec)

        it "Clones the formatter with value as the option_path and formats it":
            ret = mock.Mock(name="ret")
            cloned = mock.Mock(name="cloned")
            cloned.format.return_value = ret

            with_option_path = mock.Mock(name="with_option_path")
            with_option_path.return_value = cloned

            special_get_field = mock.Mock(name="special_get_field", return_value=None)

            args = mock.Mock(name="args")
            value = mock.Mock(name="value")
            kwargs = mock.Mock(name="kwargs")
            format_spec = mock.Mock(name="format_spec")

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
            with mock.patch.multiple(formatter, special_get_field=special_get_field, with_option_path=with_option_path):
                self.assertEqual(formatter.get_field(value, args, kwargs, format_spec=format_spec), (ret, ()))

            special_get_field.assert_called_once_with(value, args, kwargs,format_spec)
            with_option_path.assert_called_once_with(value)

    describe "format_field":
        it "returns special_format_field if it returns a value":
            ret = mock.Mock(name="ret")
            special_format_field = mock.Mock(name="special_format_field")
            special_format_field.return_value = ret

            obj = mock.Mock(name="obj")
            format_spec = mock.Mock(name="format_spec")

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
            with mock.patch.object(formatter, "special_format_field", special_format_field):
                self.assertIs(formatter.format_field(obj, format_spec), ret)

            special_format_field.assert_called_once_with(obj, format_spec)

        it "returns the obj if it's a dictionary":
            class blah(dict): pass
            obj = blah()

            format_spec = mock.Mock(name="format_spec")
            special_format_field = mock.Mock(name="special_format_field", return_value=None)

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
            with mock.patch.object(formatter, "special_format_field", special_format_field):
                self.assertIs(formatter.format_field(obj, format_spec), obj)

            special_format_field.assert_called_once_with(obj, format_spec)

        it "returns the object if asks for it":
            class Obj(object):
                _merged_options_formattable = True
            obj = Obj()

            format_spec = mock.Mock(name="format_spec")
            special_format_field = mock.Mock(name="special_format_field", return_value=None)

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
            with mock.patch.object(formatter, "special_format_field", special_format_field):
                self.assertIs(formatter.format_field(obj, format_spec), obj)

            special_format_field.assert_called_once_with(obj, format_spec)

        it "returns the object if it's a mock":
            obj = mock.Mock(name="obj")

            format_spec = mock.Mock(name="format_spec")
            special_format_field = mock.Mock(name="special_format_field", return_value=None)

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
            with mock.patch.object(formatter, "special_format_field", special_format_field):
                self.assertIs(formatter.format_field(obj, format_spec), obj)

            special_format_field.assert_called_once_with(obj, format_spec)

        it "returns the obj if it's a lambda or function or method":
            class blah(dict):
                def method(self): pass
            def func(self): pass
            lamb = lambda : 1
            obj = blah()

            format_spec = mock.Mock(name="format_spec")
            special_format_field = mock.Mock(name="special_format_field", return_value=None)

            for callable_obj in (obj.method, func, lamb, sum):
                formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
                with mock.patch.object(formatter, "special_format_field", special_format_field):
                    self.assertIs(formatter.format_field(callable_obj, format_spec), callable_obj)

        it "does an actual format_field if no special and obj is not a dict":
            obj = "shizzle"

            format_spec = mock.Mock(name="format_spec")
            special_format_field = mock.Mock(name="special_format_field", return_value=None)

            ret = mock.Mock(name="ret")
            super_format_field = mock.Mock(name="super_format_field", return_value=ret)

            formatter = MergedOptionStringFormatter(self.all_options, self.option_path)
            with mock.patch.object(string.Formatter, "format_field", super_format_field):
                with mock.patch.object(formatter, "special_format_field", special_format_field):
                    self.assertIs(formatter.format_field(obj, format_spec), ret)

            special_format_field.assert_called_once_with(obj, format_spec)

    describe "_vformat":
        it "returns the object if only formatting one item":
            blah = type("blah", (dict, ), {})()
            all_options = {"meh": blah}

            args = mock.Mock(name="args")
            kwargs = mock.Mock(name="kwargs")
            used_args = set([mock.Mock(name="used_args")])

            formatter = MergedOptionStringFormatter(all_options, "meh")
            special_get_field = mock.Mock(name="special_get_field", return_value=None)
            special_format_field = mock.Mock(name="special_format_field", return_value=None)

            with mock.patch.multiple(formatter, special_get_field=special_get_field, special_format_field=special_format_field):
                self.assertIs(formatter._vformat("{meh}", args, kwargs, used_args, 2), blah)

        it "concatenates the strings together if this is multiple things to be formatted":
            blah = type("blah", (dict, ), {})({'1':'2'})
            all_options = {"meh": blah, "wat": "ever"}

            args = mock.Mock(name="args")
            kwargs = mock.Mock(name="kwargs")
            used_args = set([mock.Mock(name="used_args")])

            formatter = MergedOptionStringFormatter(all_options, "meh")
            special_get_field = mock.Mock(name="special_get_field", return_value=None)
            special_format_field = mock.Mock(name="special_format_field", return_value=None)

            with mock.patch.multiple(formatter, special_get_field=special_get_field, special_format_field=special_format_field):
                self.assertEqual(formatter._vformat("{meh}and{wat}", args, kwargs, used_args, 2), "{'1': '2'}andever")

describe TestCase, "Custom MergedOptionStringFormatter":
    it "works":
        class MyStringFormatter(MergedOptionStringFormatter):
            def special_format_field(self, obj, format_spec):
                if format_spec == "upper":
                    return obj.upper()

                if format_spec == "no_interpret":
                    return obj

            def special_get_field(self, value, args, kwargs, format_spec=None):
                if format_spec == "no_interpret":
                    return value, ()

        all_options = MergedOptions.using({"yeap": "yessir", "blah": "notused"}, {"blah": {"things": "stuff", "la": "delala"}})
        formatter = MyStringFormatter(all_options, "whatever", value="{yeap} and {blah.things:upper} {blah.la:no_interpret}")
        self.assertEqual(formatter.format(), "yessir and STUFF blah.la")

    it "formats what it finds":
        class MyStringFormatter(MergedOptionStringFormatter):
            def special_format_field(self, obj, format_spec):
                pass

            def special_get_field(self, value, args, kwargs, format_spec=None):
                pass

        all_options = MergedOptions.using({"one": "{two}", "two": "three"})
        formatter = MyStringFormatter(all_options, "one", value="{one}")
        self.assertEqual(formatter.format(), "three")

