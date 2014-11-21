# coding: spec

from option_merge.joiner import dot_joiner, join
from option_merge.path import Path

import itertools

from delfick_error import DelfickErrorTestMixin
import unittest
import mock

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "dot_joiner":
    it "joins keeping only one dot in between":
        blah_possibilities = ["blah", ".blah", "blah.", ".blah.", "blah..", "..blah", "..blah.."]
        stuff_possibilities = [pos.replace("blah", "stuff") for pos in blah_possibilities]

        for pos in blah_possibilities:
            self.assertEqual(dot_joiner([pos]), "blah")

        for blahpos, stuffpos in (list(itertools.product(blah_possibilities, stuff_possibilities))):
            self.assertEqual(dot_joiner([blahpos, stuffpos]), "blah.stuff")#

    it "ignores strings":
        self.assertEqual(dot_joiner("blah"), "blah")

describe TestCase, "join":
    it "Joins as lists":
        self.assertEqual(join(Path([]), Path([])), Path([]))
        self.assertEqual(join(Path([""]), Path([])), Path([]))
        self.assertEqual(join(Path([""]), Path([""])), Path([]))

        self.assertEqual(join(Path(["a", "b", "c"]), Path(["d", "e", "f"])), Path(["a", "b", "c", "d", "e", "f"]))
        self.assertEqual(join(Path(["a", "b", "c"]), ["d", "e", "f"]), Path(["a", "b", "c", "d", "e", "f"]))
        self.assertEqual(join(["a", "b", "c"], Path(["d", "e", "f"])), Path(["a", "b", "c", "d", "e", "f"]))
        self.assertEqual(join(["a", "b", "c"], ["d", "e", "f"]), Path(["a", "b", "c", "d", "e", "f"]))

    it "Joins as strings":
        self.assertEqual(join(Path(""), Path("")), Path(""))
        self.assertEqual(join(Path("a.b.c"), Path("d.e.f")), Path("a.b.c.d.e.f"))
        self.assertEqual(join("a.b.c", Path("d.e.f")), Path("a.b.c.d.e.f"))
        self.assertEqual(join("a.b.c", "d.e.f"), Path("a.b.c.d.e.f"))
        self.assertEqual(join(Path("a.b.c"), "d.e.f"), Path("a.b.c.d.e.f"))

