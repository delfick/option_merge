# coding: spec

from option_merge.converter import Converters
from option_merge.not_found import NotFound
from option_merge.joiner import dot_joiner
from option_merge.path import Path

from noseOfYeti.tokeniser.support import noy_sup_setUp
from delfick_error import DelfickErrorTestMixin
import unittest
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "Path":
	it "takes in path, configuration, converters and ignore_converters":
		path = mock.Mock(name="path")
		converters = mock.Mock(name="converters")
		configuration = mock.Mock(name="configuration")
		ignore_converters = mock.Mock(name="ignore_converters")
		path_obj = Path(path, configuration, converters, ignore_converters)

		self.assertEqual(path_obj.path, path)
		self.assertIs(path_obj.converters, converters)
		self.assertIs(path_obj.configuration, configuration)
		self.assertIs(path_obj.ignore_converters, ignore_converters)

	describe "Convert factory method":
		it "returns the same object if already a Path object":
			path = mock.Mock(name="path")
			converters = mock.Mock(name="converters")
			configuration = mock.Mock(name="configuration")
			ignore_converters = mock.Mock(name="ignore_converters")
			path_obj = Path(path, configuration, converters, ignore_converters)
			converted = Path.convert(path_obj)
			assert converted is path_obj

	describe "Special methods":
		it "dot joins the path for __unicode__":
			self.assertEqual(str(Path("a.b.c.d")), "a.b.c.d")
			self.assertEqual(str(Path(["a.b", "c", "d"])), "a.b.c.d")
			self.assertEqual(str(Path(["a", "b", "c", "d"])), "a.b.c.d")
			self.assertEqual(str(Path([["a", "b"], "c", "d"])), "ab.c.d")

		it "returns boolean status of path for __nonzero__":
			assert Path("asdf")
			assert Path(["a", "b"])
			assert not Path("")
			assert not Path([])

		it "returns the length of path parts for __len__":
			self.assertEqual(len(Path("adsf")), 1)
			self.assertEqual(len(Path("")), 0)
			self.assertEqual(len(Path(["a.b", "c", "d"])), 3)

		it "yields each part of path parts for __iter__":
			self.assertEqual(list(Path("adsf")), ["adsf"])
			self.assertEqual(list(Path("")), [])
			self.assertEqual(list(Path(["a.b", "c", "d"])), ["a.b", "c", "d"])

		it "includes str of Path for repr":
			self.assertEqual(repr(Path("asdf.asdf.1")), "<Path(asdf.asdf.1)>")
			self.assertEqual(repr(Path(["asdf", "asdf", "1"])), "<Path(asdf.asdf.1)>")

		it "converts dot_joined of paths to determine equality":
			self.assertEqual(Path("asdf.adsf.1"), "asdf.adsf.1")
			self.assertEqual(Path(["asdf", "adsf", "1"]), "asdf.adsf.1")

			self.assertEqual(Path("asdf.adsf.1"), ["asdf", "adsf", "1"])
			self.assertEqual(Path(["asdf", "adsf", "1"]), ["asdf", "adsf", "1"])

			self.assertEqual(Path("asdf.adsf.1"), Path("asdf.adsf.1"))
			self.assertEqual(Path(["asdf", "adsf", "1"]), Path(["asdf", "adsf", "1"]))

		it "converts dot_joined of paths to determine inequality":
			with self.fuzzyAssertRaisesError(AssertionError, "<Path\(asdf.adsf.1\)> == 'asdf.adsf.1'"):
				self.assertNotEqual(Path("asdf.adsf.1"), "asdf.adsf.1")

			self.assertNotEqual(Path("asdf.adsf.2"), "asdf.adsf.1")
			self.assertNotEqual(Path(["asdf", "adsf", "3"]), "asdf.adsf.1")

			self.assertNotEqual(Path("asdf.adsf.4"), ["asdf", "adsf", "1"])
			self.assertNotEqual(Path(["asdf", "adsf", "5"]), ["asdf", "adsf", "1"])

			self.assertNotEqual(Path("asdf.adsf.6"), Path("asdf.adsf.1"))
			self.assertNotEqual(Path(["asdf", "adsf", "7"]), Path(["asdf", "adsf", "1"]))

		it "joins self to other and creates a clone using the result for __add__":
			path = mock.Mock(name="path")
			other = mock.Mock(name="other")
			clone = mock.Mock(name="clone")
			joined = mock.Mock(name="joined")

			join = mock.Mock(name="join", return_value=joined)
			using = mock.Mock(name="using", return_value=clone)

			path_obj = Path(path)
			with mock.patch("option_merge.path.join", join):
				with mock.patch.multiple(path_obj, using=using):
					self.assertIs(path_obj + other, clone)

			using.assert_called_once_with(joined)
			join.assert_called_once_with(path_obj, other)

		it "uses the dot_join of the path for hashing the path":
			path = mock.Mock(name="path")
			self.assertEqual(hash(Path(path)), hash(dot_joiner(path)))
			self.assertEqual(hash(Path(["1", "2", "3"])), hash("1.2.3"))
			self.assertEqual(hash(Path("1.2.3")), hash("1.2.3"))

	describe "without":
		it "uses string_slicing if path is a string":
			self.assertEqual(Path("1.2.3").without("1.2"), Path("3"))
			self.assertEqual(Path("1.2.3").without(Path("1.2")), Path("3"))
			self.assertEqual(Path("1.2.3").without(Path(["1", "2"])), Path("3"))

		it "works with string base against list path":
			self.assertEqual(Path(["1", "2", "3"]).without("1.2"), Path("3"))
			self.assertEqual(Path(["1", "2", "3"]).without(Path("1.2")), Path("3"))

		it "raises NotFound if the prefix is not in the path":
			with self.fuzzyAssertRaisesError(NotFound):
				Path(["1", "2", "3"]).without("1.2.3.4")

			with self.fuzzyAssertRaisesError(NotFound):
				Path(["1", "2", "3"]).without("5.2")

		it "returns the path if base is empty":
			self.assertEqual(Path("a.b").without(""), Path("a.b"))
			self.assertEqual(Path("a.b").without([]), Path("a.b"))
			self.assertEqual(Path("a.b").without(Path("")), Path("a.b"))

			self.assertEqual(Path(["a", "b"]).without(""), Path("a.b"))
			self.assertEqual(Path(["a", "b"]).without([]), Path("a.b"))
			self.assertEqual(Path(["a", "b"]).without(Path("")), Path("a.b"))

	describe "Prefixed":
		it "returns a clone with the prefix joined to the path":
			path = mock.Mock(name="path")
			clone = mock.Mock(name="clone")
			prefix = mock.Mock(name="prefix")
			joined = mock.Mock(name="joined")

			join = mock.Mock(name="join", return_value=joined)
			using = mock.Mock(name="using", return_value=clone)

			path_obj = Path(path)
			with mock.patch("option_merge.path.join", join):
				with mock.patch.multiple(path_obj, using=using):
					self.assertIs(path_obj.prefixed(prefix), clone)

			using.assert_called_once_with(joined)
			join.assert_called_once_with(prefix, path_obj)

	describe "startswith":
		it "says whether the dot join of the path startswith the base":
			self.assertEqual(Path(["a.b", "c.d"]).startswith("a.b.c"), True)
			self.assertEqual(Path("a.b.c.d").startswith("a.b.c"), True)

			self.assertEqual(Path(["a.b", "c.d"]).startswith("b.c.d"), False)
			self.assertEqual(Path("a.b.c.d").startswith("b.c.d"), False)

	describe "endswith":
		it "says whether the dot join of the path endswith the suffix":
			self.assertEqual(Path(["a.b", "c.d"]).endswith("b.c.d"), True)
			self.assertEqual(Path("a.b.c.d").endswith("b.c.d"), True)

			self.assertEqual(Path(["a.b", "c.d"]).endswith("a.b.c"), False)
			self.assertEqual(Path("a.b.c.d").endswith("a.b.c"), False)

	describe "using":
		it "returns the same class with the new path and other same values and ignore_converters as True":
			p1 = mock.Mock(name="p1")
			p2 = mock.Mock(name="p2")
			conf = mock.Mock(name="conf")
			converters = mock.Mock(name="converters")
			ignore_converters = mock.Mock(name="ignore_converters")

			class Path2(Path): pass
			path = Path2(p1, conf, converters, ignore_converters=ignore_converters)
			new_path = path.using(p2)

			self.assertEqual(type(new_path), Path2)
			self.assertIs(new_path.path, p2)
			self.assertIs(new_path.configuration, conf)
			self.assertIs(new_path.converters, converters)
			self.assertIs(new_path.ignore_converters, False)

		it "returns the same class with the new path and other overrides":
			p1 = mock.Mock(name="p1")
			p2 = mock.Mock(name="p2")
			conf = mock.Mock(name="conf")
			conf2 = mock.Mock(name="conf2")
			converters = mock.Mock(name="converters")
			converters2 = mock.Mock(name="converters2")
			ignore_converters = mock.Mock(name="ignore_converters")
			ignore_converters2 = mock.Mock(name="ignore_converters2")

			class Path2(Path): pass
			path = Path2(p1, conf, converters, ignore_converters=ignore_converters)
			new_path = path.using(p2, conf2, converters2, ignore_converters2)

			self.assertEqual(type(new_path), Path2)
			self.assertIs(new_path.path, p2)
			self.assertIs(new_path.configuration, conf2)
			self.assertIs(new_path.converters, converters2)
			self.assertIs(new_path.ignore_converters, ignore_converters2)

	describe "Clone":
		it "Returns a new path with same everything":
			p1 = mock.Mock(name="p1")
			conf = mock.Mock(name="conf")
			converters = mock.Mock(name="converters")
			ignore_converters = mock.Mock(name="ignore_converters")

			path = Path(p1, conf, converters, ignore_converters=ignore_converters)
			new_path = path.clone()
			self.assertIs(path.path, new_path.path)
			self.assertIs(path.converters, new_path.converters)
			self.assertIs(path.configuration, new_path.configuration)
			self.assertIs(path.ignore_converters, new_path.ignore_converters)

	describe "ignoring_converters":
		it "returns a clone with the same path and ignore_converters default to True":
			p1 = mock.Mock(name="p1")
			conf = mock.Mock(name="conf")
			converters = mock.Mock(name="converters")
			path = Path(p1, conf, converters, False)

			new_path = path.ignoring_converters()
			assert new_path is not path
			self.assertIs(new_path.path, p1)
			self.assertIs(new_path.configuration, conf)
			self.assertIs(new_path.converters, converters)
			self.assertIs(new_path.ignore_converters, True)

		it "can be given an ignore_converters to use":
			p1 = mock.Mock(name="p1")
			conf = mock.Mock(name="conf")
			converters = mock.Mock(name="converters")
			path = Path(p1, conf, converters, False)

			ignore_converters2 = mock.Mock(name="ignore_converters2")
			new_path = path.ignoring_converters(ignore_converters=ignore_converters2)
			assert new_path is not path
			self.assertIs(new_path.path, p1)
			self.assertIs(new_path.configuration, conf)
			self.assertIs(new_path.converters, converters)
			self.assertIs(new_path.ignore_converters, ignore_converters2)

	describe "Doing a conversion":
		it "returns value as is if there are no converters":
			p1 = mock.Mock(name="p1")
			value = mock.Mock(name="value")

			find_converter = mock.Mock(name="find_converter")
			find_converter.return_value = (None, False)

			path = Path(p1)
			with mock.patch.object(path, "find_converter", find_converter):
				self.assertEqual(path.do_conversion(value), (value, False))

		it "uses found converter and marks path as done with converters":
			p1 = mock.Mock(name="p1")
			value = mock.Mock(name="value")
			converters = Converters()
			converters.activate()

			path = Path(p1, converters=converters)
			self.assertEqual(converters.converted(path), False)

			converted = mock.Mock(name="converted")
			converter = mock.Mock(name="converter")
			converter.return_value = converted

			find_converter = mock.Mock(name="find_converter")
			find_converter.return_value = (converter, True)

			with mock.patch.object(path, "find_converter", find_converter):
				self.assertEqual(path.do_conversion(value), (converted, True))

			# Converters should now have converted value
			self.assertEqual(converters.converted(path), True)
			self.assertIs(converters.converted_val(path), converted)

			converter.assert_called_once_with(path, value)
			converted.post_setup.assert_called_once_with()

	describe "finding a converter":
		before_each:
			self.p1 = mock.Mock(name="p1")
			self.converter1 = mock.Mock(name="converter1")
			self.converter2 = mock.Mock(name="converter2")
			self.converter3 = mock.Mock(name="converter3")
			self.converters = Converters()
			self.converters.append(self.converter1)
			self.converters.append(self.converter2)
			self.converters.append(self.converter3)

			self.converters.activate()
			self.path = Path(self.p1, converters=self.converters)

		it "returns None if set to ignore_converters":
			self.assertEqual(self.path.ignoring_converters().find_converter(), (None, False))

		it "returns the first converter that has no matches attribute":
			self.assertEqual(self.path.find_converter(), (self.converter1, True))

		it "returns the first converter that matches the path":
			self.converter1.matches.return_value = False
			self.converter2.matches.return_value = True
			self.assertEqual(self.path.find_converter(), (self.converter2, True))

			self.converter1.matches.assert_called_once_with(self.path)
			self.converter2.matches.assert_called_once_with(self.path)

		it "returns None if no converter matches":
			self.converter1.matches.return_value = False
			self.converter2.matches.return_value = False
			self.converter3.matches.return_value = False
			self.assertEqual(self.path.find_converter(), (None, False))

			self.converter1.matches.assert_called_once_with(self.path)
			self.converter2.matches.assert_called_once_with(self.path)
			self.converter3.matches.assert_called_once_with(self.path)

	describe "Finding converted value":
		it "returns False if there are no converters":
			p1 = mock.Mock(name="p1")
			path = Path(p1, converters=None)
			self.assertEqual(path.converted(), False)

		it "returns what converters returns":
			p1 = mock.Mock(name="p1")
			result = mock.Mock(name="result")
			converters = mock.Mock(name="converters")
			converters.converted.return_value = result

			path = Path(p1, converters=converters)
			self.assertIs(path.converted(), result)

	describe "Finding a converted value":
		it "returns what converters returns":
			p1 = mock.Mock(name="p1")
			result = mock.Mock(name="result")
			converters = mock.Mock(name="converters")
			converters.converted_val.return_value = result

			path = Path(p1, converters=converters)
			self.assertIs(path.converted_val(), result)

