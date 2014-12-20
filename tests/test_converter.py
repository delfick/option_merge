# coding: spec

from option_merge.converter import Converter, Converters
from option_merge.path import Path

from noseOfYeti.tokeniser.support import noy_sup_setUp
from delfick_error import DelfickErrorTestMixin
import unittest
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "Converter":
	it "takes in conversion logic and convert_path":
		convert = mock.Mock(name="convert")
		convert_path = mock.Mock(name="convert_path")
		converter = Converter(convert, convert_path)
		self.assertIs(converter.convert, convert)
		self.assertIs(converter.convert_path, convert_path)

	it "proxies convert on call":
		path = mock.Mock(name="path")
		data = mock.Mock(name="data")
		convert = mock.Mock(name="convert")
		result = mock.Mock(name="result")
		convert.return_value = result

		self.assertIs(Converter(convert)(path, data), result)
		convert.assert_called_once_with(path, data)

	describe "Matching against a path":
		it "works with Path against Path":
			assert Converter(None, Path("a.b.c.d")).matches(Path("a.b.c.d"))
			assert Converter(None, Path("a.b.c.d")).matches(Path(["a.b", "c", "d"]))
			assert Converter(None, Path(["a", "b", "c", "d"])).matches(Path("a.b.c.d"))
			assert Converter(None, Path(["a", "b", "c", "d"])).matches(Path(["a", "b", "c", "d"]))

			assert not Converter(None, Path("a.c.d")).matches(Path("a.b.c.d"))
			assert not Converter(None, Path("a.c.d")).matches(Path(["a.b", "c", "d"]))
			assert not Converter(None, Path(["a", "c", "d"])).matches(Path("a.b.c.d"))
			assert not Converter(None, Path(["a", "c", "d"])).matches(Path(["a", "b", "c", "d"]))

		it "works with Path against list":
			assert Converter(None, Path("a.b.c.d")).matches(["a", "b", "c", "d"])
			assert Converter(None, Path(["a", "b", "c", "d"])).matches(["a", "b", "c", "d"])
			assert not Converter(None, Path(["a", "c", "d"])).matches(["a", "b", "c", "d"])
			assert not Converter(None, Path("a.c.d")).matches(["a", "b", "c", "d"])

		it "works with Path against string":
			assert Converter(None, Path("a.b.c.d")).matches("a.b.c.d")
			assert Converter(None, Path(["a", "b", "c", "d"])).matches("a.b.c.d")
			assert not Converter(None, Path(["a", "c", "d"])).matches("a.b.c.d")
			assert not Converter(None, Path("a.c.d")).matches("a.b.c.d")

		it "works with string against list":
			assert Converter(None, "a.b.c.d").matches(["a.b", "c", "d"])
			assert not Converter(None, "a.c.d").matches(["a.b", "c", "d"])

		it "works with string against string":
			assert Converter(None, Path("a.b.c.d")).matches("a.b.c.d")
			assert not Converter(None, Path("a.c.d")).matches("a.b.c.d")

		it "works with list against list":
			assert Converter(None, ["a", "b", "c", "d"]).matches(["a", "b", "c", "d"])
			assert not Converter(None, ["a", "c", "d"]).matches(["a", "b", "c", "d"])

describe TestCase, "Converters":
	it "defaults activated to False":
		self.assertEqual(Converters().activated, False)

	describe "Iteration":
		it "yields nothing if not activated":
			self.assertEqual(list(Converters()), [])

			converters = Converters()
			converters.append(1)
			converters.append(2)
			converters.append(3)
			self.assertEqual(converters.activated, False)
			self.assertEqual(list(converters), [])

		it "yields all the converters if activated":
			converters = Converters()
			converters.append(1)
			converters.append(2)
			converters.append(3)
			self.assertEqual(converters.activated, False)
			self.assertEqual(list(converters), [])

			converters.activate()
			self.assertEqual(converters.activated, True)
			self.assertEqual(list(converters), [1, 2, 3])

	describe "Adding converters":
		it "just adds to internal list":
			converters = Converters()
			self.assertEqual(converters._converters, [])
			converter1 = mock.Mock(name="converter1")
			converter2 = mock.Mock(name="converter2")

			converters.append(converter1)
			self.assertEqual(converters._converters, [converter1])

			converters.append(converter2)
			self.assertEqual(converters._converters, [converter1, converter2])

	describe "Activation":
		it "just sets activated to True":
			converters = Converters()
			self.assertEqual(converters.activated, False)

			converters.activate()
			self.assertEqual(converters.activated, True)

	describe "Marking a path as done":
		it "stores a value for that path in _converted":
			val = mock.Mock(name="val")
			converters = Converters()
			self.assertEqual(converters._converted, {})

			converters.done(Path("1.2.3.4"), val)
			self.assertEqual(converters._converted, {Path("1.2.3.4"): val})

	describe "Determining state of a path":
		it "says no if not activated":
			converters = Converters()
			path = Path("1.2.3")
			self.assertEqual(converters.converted(path), False)

			val = mock.Mock(name="val")
			converters.done("1.2.3", val)
			self.assertEqual(converters.activated, False)
			self.assertEqual(converters.converted(path), False)

		it "says yes if there is a converted val for the path":
			converters = Converters()
			path = Path("1.2.3")
			self.assertEqual(converters.converted(path), False)

			val = mock.Mock(name="val")
			converters.done("1.2.3", val)
			self.assertEqual(converters.activated, False)
			self.assertEqual(converters.converted(path), False)

			converters.activate()
			self.assertEqual(converters.converted(path), True)

	describe "Retrieving converted value":
		it "returns the converted value":
			val = mock.Mock(name="val")
			converters = Converters()
			converters.done(Path("1.2.3"), val)

			self.assertIs(converters.converted_val(Path("1.2.3")), val)
			self.assertIs(converters.converted_val("1.2.3"), val)

