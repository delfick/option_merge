# coding: spec

from option_merge.collector import Collector
from option_merge import MergedOptions

from delfick_error import DelfickErrorTestMixin, DelfickError
from noseOfYeti.tokeniser.support import noy_sup_setUp
from contextlib import contextmanager
from getpass import getpass
import tempfile
import unittest
import shutil
import mock
import json
import os

class TestCase(unittest.TestCase, DelfickErrorTestMixin): pass

describe TestCase, "Collector":
    @contextmanager
    def fake_config(self, body="\n{}"):
        root = None
        try:
            root = tempfile.mkdtemp()
            config_file = os.path.join(root, "config.json")
            with open(config_file, 'w') as fle:
                fle.write(body)
            yield (root, config_file)
        finally:
            if root and os.path.exists(root):
                shutil.rmtree(root)

    describe "Cloning":
        it "returns an instance that has rerun collect_configuration and prepare":
            called = []
            original_cli_args = {'a': 1, "b": 2}
            with self.fake_config() as (config_root, config_file):
                class Col(Collector):
                    def start_configuration(self): return MergedOptions.using({})
                    def read_file(self, location): return json.load(open(location))
                    def add_configuration(self, configuration, collect_another_source, done, result, src): configuration.update(result)

                    def alter_clone_cli_args(slf, nw_cllctr, nw_cli_args, new_args):
                        nw_cli_args.update(new_args)
                        called.append((1, nw_cllctr, nw_cli_args))

                collector = Col()
                collector.prepare(config_file, original_cli_args)
                self.assertEqual(collector.configuration["cli_args"].as_dict(), original_cli_args)

            class MockCollectorKls(Col):
                def prepare(slf, config_file, new_cli_args):
                    called.append((2, (config_file, new_cli_args)))

            collector.__class__ = MockCollectorKls

            clone = collector.clone({"c": 3, "b": 4})
            self.assertIs(type(clone), MockCollectorKls)
            self.assertEqual(called, [
                    (1, clone, {"a": 1, "b": 4, "c": 3})
                  , (2, (config_file, {"a": 1, "b": 4, "c": 3}))
                  ]
                )
            self.assertEqual(original_cli_args, {"a": 1, "b": 2})

    describe "prepare":
        it "find_missing_config, updates configuration, does extra_prepare, activates converters and extra_prepare_after_activation":
            called = []
            with self.fake_config('{"one": 1}') as (config_root, config_file):
                class Col(Collector):
                    def start_configuration(self): return MergedOptions.using({})
                    def read_file(self, location): return json.load(open(location))
                    def add_configuration(self, configuration, collect_another_source, done, result, src): configuration.update(result)

                    def find_missing_config(slf, config):
                        called.append((1, config))
                        self.assertEqual(config.as_dict(), {"config_root": config_root, "one": 1})
                        config.converters = mock.Mock(name="converters")

                    def extra_prepare(slf, config, cli_args):
                        called.append((2, config, cli_args))
                        self.assertEqual(config.as_dict()
                            , { "getpass": getpass
                              , "collector": slf
                              , "cli_args": cli_args
                              , "config_root": config_root
                              , "one": 1
                              }
                            )
                        self.assertEqual(len(config.converters.mock_calls), 0)

                    def extra_prepare_after_activation(slf, config, cli_args):
                        called.append((3, config, cli_args))
                        config.converters.activate.assert_called_once()

                collector = Col()
                self.assertEqual(called, [])

                cli_args = mock.Mock(name="cli_args")
                collector.prepare(config_file, cli_args)
                self.assertEqual(called, [(1, collector.configuration), (2, collector.configuration, cli_args), (3, collector.configuration, cli_args)])

    describe "Collecting configuration":
        it "uses start_configuration, read_file, home_dir_configuration, config_file, add_configuration and extra_configuration_collection":
            called = []
            configuration = MergedOptions.using({})

            result_home_dir = mock.MagicMock(name="result_home_dir")
            result_config_file = mock.MagicMock(name="result_config_file")

            with self.fake_config() as (config_root, config_file):
                home_dir = os.path.join(config_root, 'home.json')
                with open(home_dir, "w") as fle:
                    fle.write("{}")
                results = {config_file: result_config_file, home_dir: result_home_dir}

                class Col(Collector):
                    def start_configuration(slf):
                        called.append((1, ))
                        return configuration

                    def read_file(slf, location):
                        called.append((2, location))
                        return results[location]

                    def add_configuration(slf, config, collect_another_source, done, result, src):
                        called.append((3, config, result, src))

                    def home_dir_configuration_location(slf): return home_dir

                    def extra_configuration_collection(slf, config):
                        self.assertEqual([c[0] for c in called], [1, 2, 3, 2, 3])
                        called.append((4, config))

                collector = Col()
                collector.collect_configuration(config_file)
                self.assertEqual(called
                    , [ (1, )
                      , (2, home_dir)
                      , (3, configuration, result_home_dir, home_dir)
                      , (2, config_file)
                      , (3, configuration, result_config_file, config_file)
                      , (4, configuration)
                      ]
                    )

        it "ignores home_dir if it's not specified":
            called = []
            configuration = MergedOptions.using({})

            result_config_file = mock.MagicMock(name="result_config_file")

            with self.fake_config() as (config_root, config_file):
                results = {config_file: result_config_file}

                class Col(Collector):
                    def start_configuration(slf):
                        called.append((1, ))
                        return configuration

                    def read_file(slf, location):
                        called.append((2, location))
                        return results[location]

                    def add_configuration(slf, config, collect_another_source, done, result, src):
                        called.append((3, config, result, src))

                    def extra_configuration_collection(slf, config):
                        self.assertEqual([c[0] for c in called], [1, 2, 3])
                        called.append((4, config))

                collector = Col()
                collector.collect_configuration(config_file)
                self.assertEqual(called
                    , [ (1, )
                      , (2, config_file)
                      , (3, configuration, result_config_file, config_file)
                      , (4, configuration)
                      ]
                    )

        it "gives a function for adding more sources to add_configuration":
            called = []
            configuration = MergedOptions.using({})

            with self.fake_config() as (config_root, config_file):
                another_loc = os.path.join(config_root, 'another.json')
                with open(another_loc, "w") as fle: fle.write("{}")

                other_loc = os.path.join(config_root, 'other.json')
                with open(other_loc, "w") as fle: fle.write("{}")

                results = {config_file: {"extra": other_loc}, other_loc: {"nested": another_loc}, another_loc: {"stuff": "a"}}

                class Col(Collector):
                    def start_configuration(slf):
                        called.append((1, ))
                        return configuration

                    def read_file(slf, location):
                        called.append((2, location))
                        return results[location]

                    def add_configuration(slf, config, collect_another_source, done, result, src):
                        if "extra" in result:
                            collect_another_source(result["extra"])
                        if "nested" in result:
                            collect_another_source(result["nested"], prefix=["once", "twice"], extra={"a": "b"})
                        called.append((3, config, result, src))

                    def extra_configuration_collection(slf, config):
                        self.assertEqual([c[0] for c in called], [1, 2, 2, 2, 3, 3, 3])
                        called.append((4, config))

                collector = Col()
                collector.collect_configuration(config_file)
                self.assertEqual(called
                    , [ (1, )
                      , (2, config_file)
                      , (2, other_loc)
                      , (2, another_loc)
                      , (3, configuration, {"once": {"twice": {"stuff": "a", "a": "b", "config_root": config_root}}}, another_loc)
                      , (3, configuration, {"nested": another_loc, "config_root": config_root}, other_loc)
                      , (3, configuration, {"extra": other_loc, "config_root": config_root}, config_file)
                      , (4, configuration)
                      ]
                    )

        it "Can't create a circular loop using collect_another_source":
            called = []
            configuration = MergedOptions.using({})

            with self.fake_config() as (config_root, config_file):
                other_loc = os.path.join(config_root, 'other.json')
                with open(other_loc, "w") as fle:
                    fle.write("{}")
                results = {config_file: {"extra": other_loc}, other_loc: {"extra": config_file}}

                class Col(Collector):
                    def start_configuration(slf):
                        called.append((1, ))
                        return configuration

                    def read_file(slf, location):
                        called.append((2, location))
                        return results[location]

                    def add_configuration(slf, config, collect_another_source, done, result, src):
                        self.assertEqual(result["config_root"], config_root)
                        collect_another_source(result["extra"])
                        called.append((3, config, result, src))

                    def extra_configuration_collection(slf, config):
                        self.assertEqual([c[0] for c in called], [1, 2, 2, 3, 3])
                        called.append((4, config))

                collector = Col()
                collector.collect_configuration(config_file)
                self.assertEqual(called
                    , [ (1, )
                      , (2, config_file)
                      , (2, other_loc)
                      , (3, configuration, {"extra": config_file, "config_root": config_root}, other_loc)
                      , (3, configuration, {"extra": other_loc, "config_root": config_root}, config_file)
                      , (4, configuration)
                      ]
                    )

        it "collects errors from reading files and raises a mother exception":
            class BadJson(DelfickError): pass
            class BadConfiguration(DelfickError): pass

            called = []
            with self.fake_config() as (config_root, config_file):
                home_dir = os.path.join(config_root, 'home.json')
                with open(home_dir, "w") as fle:
                    fle.write("{}")

                class Col(Collector):
                    BadFileErrorKls = BadJson
                    BadConfigurationErrorKls = BadConfiguration

                    def start_configuration(slf): called.append(0); return MergedOptions.using({})
                    def read_file(slf, location): called.append((1, location)); raise BadJson(location=location)
                    def add_configuration(slf, *args, **kwargs): assert False, "This shouldn't get called"
                    def extra_configuration_collection(slf, config): called.append(2)
                    def home_dir_configuration_location(slf): return home_dir

                with self.fuzzyAssertRaisesError(BadConfiguration, "Some of the configuration was broken", _errors=[BadJson(location=home_dir), BadJson(location=config_file)]):
                    collector = Col()
                    collector.collect_configuration(config_file)
                self.assertEqual(called, [0, (1, home_dir), (1, config_file), 2])
