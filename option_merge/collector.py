"""
The collector object is responsible for collecting configuration
and setting up converters

For example:

.. code-block:: python

    class JsonCollector(Collector):
        def start_configuration(self):
            return MergedOptions()

        def find_missing_config(self, configuration):
            assert "important_option" in configuration

        def extra_prepare(self, configuration, args_dict):
            configuration.update(
                  {"some_option": args_dict["some_option"]}
                , source=<extra_prepare>
                )

        def read_file(self, location):
            return json.loads(location)

        def add_configuration(self, configuration, collect_another_source, done, result, src):
            configuration.update(result, source=src)
            for loc in result.get("others", []):
                collect_another_source(
                      os.path.join(os.path.dirname(src), loc)
                    , prefix=os.path.splitext(loc)[1]
                    )

        def extra_configuration_collection(self, configuration):
            def convert(p, v):
                return v * 2
            configuration.add_converter(
                  Converter(
                      convert=convert
                    , convert_path=["some", "contrived", "example"]
                    )
                )

    collector = JsonCollector()
    collector.prepare(
          "/path/to/first_config_file.json"
        , {"some_option": "stuff"}
        )

    #### /path/to/first_config_file.json
    # { "hello": "there"
    # , "others": ["some.json"]
    # }

    #### /path/to/some.json
    # { "contrived":
    #   { "example": 2
    #   }
    # }

    collector.configuration["some_option"] == "stuff"
    collector.configuration["some.contrived.example"] == 4
"""

from option_merge.versioning import VersionedDict
from option_merge.converter import Converter

from getpass import getpass
import logging
import os

log = logging.getLogger("option_merge.collector")

class Collector(object):
    """
    When using the Collector, it is expected that you implement a number of hooks
    to make this class useful.
    """
    class BadFileErrorKls(Exception):
        _fake_delfick_error = True
        def __init__(self, message):
            self.message = message
            self.kwargs = {}
        def __str__(self):
            return "BadFile: {0}".format(self.message)

    class BadConfigurationErrorKls(Exception):
        _fake_delfick_error = True
        def __init__(self, _errors):
            self.message = ""
            self.kwargs = {}
            self.errors = _errors
        def __str__(self):
            message = "errors:\n=======\n\n\t{0}".format("\n\t".join("{0}\n-------".format('\n\t'.join(str(error).split('\n'))) for error in self.errors))
            return "BadConfiguration:\n{0}".format(message)

    def __init__(self):
        self.setup()

    ########################
    ###   HOOKS
    ########################

    def setup(self):
        """Called at __init__ time"""

    def alter_clone_args_dict(self, new_collector, new_args_dict, *args, **kwargs):
        """
        Hook for altering args_dict given to a clone collector it must return a dictionary

        This dictionary will be used in the ``prepare`` call for the new collector
        """
        return new_args_dict

    def find_missing_config(self, configuration):
        """Hook to raise errors about missing configuration"""

    def extra_prepare(self, configuration, args_dict):
        """Hook for any extra preparation before the converters are activated"""

    def extra_prepare_after_activation(self, configuration, args_dict):
        """Hook for any extra preparation after the converters are activated"""

    def home_dir_configuration_location(self):
        """Hook to return the location of the configuration in the user's home directory"""
        return None

    def read_file(self, location):
        """Hook to read in a file and return a dictionary"""
        raise NotImplementedError()

    def start_configuration(self):
        """Hook for starting the base of the configuration"""
        raise NotImplementedError()

    def add_configuration(self, configuration, collect_another_source, done, result, src):
        """
        Hook to add to the configuration the loaded result from src into configuration

        The collect_another_source function can be used to collect another source

        And done is a dictionary of configuration we have already added
        """
        raise NotImplementedError()

    def extra_configuration_collection(self, configuration):
        """Hook to do any extra configuration collection or converter registration"""

    ########################
    ###   USAGE
    ########################

    def clone(self, *args, **kwargs):
        """Create a new collector that is a clone of this one"""
        if not hasattr(self, "configuration_file"):
            return self.__class__()
        new_collector = self.__class__()
        args_dict_clone = dict(self.configuration["args_dict"].items())
        new_args_dict = self.alter_clone_args_dict(new_collector, args_dict_clone, *args, **kwargs)
        new_collector.prepare(self.configuration_file, new_args_dict)
        return new_collector

    def prepare(self, configuration_file, args_dict):
        """
        Prepare the collector!

        * Collect all the configuration
        * find missing configuration
        * do self.extra_prepare
        * Activate the converters
        * Do self.extra_prepare_after_activation
        """
        self.configuration_file = configuration_file
        self.configuration = self.collect_configuration(configuration_file, args_dict)

        self.find_missing_config(self.configuration)

        self.extra_prepare(self.configuration, args_dict)
        self.configuration.converters.activate()
        self.extra_prepare_after_activation(self.configuration, args_dict)

        for addon, result, kwargs in getattr(self, "registered_addons", []):
            result.post_register(self.configuration, **kwargs)

    def register_addons(self, AddonGetter, addons, Meta, configuration, **kwargs):
        """
        Resolve and add addons into the configuration.

        Addons should be a list of strings to entry_points at option_merge.addons
        """
        self.registered_addons = getattr(self, "registered_addons", [])

        def register(adns):
            moar = []
            for addon in adns:
                if addon in [name for name in self.registered_addons]:
                    continue

                for result in AddonGetter.get(addon, configuration, **kwargs):
                    self.registered_addons.insert(0, (addon, result, kwargs))
                    self.register_converters(result.specs, Meta, configuration)
                    moar.extend(result.addons)
            return moar

        nxt = addons
        while True:
            nxt = register(nxt)
            if not nxt:
                break

    def register_converters(self, specs, Meta, configuration):
        """
        Register converters

        specs
            a Dictionary of {(priority, [path]): spec}

        Meta
            The class to instantiate to create ``meta``

            The converter will call ``spec.normalise(meta, val)``

        configuration
            The configuration to add the converter to
        """
        for (_, key), spec in sorted(specs.items()):
            def make_converter(k, s):
                def converter(p, v):
                    log.info("Converting %s", p)
                    meta = Meta(p.configuration, [])
                    for kk in k:
                        meta = meta.at(kk)
                    configuration.converters.started(p)
                    return s.normalise(meta, v)
                configuration.add_converter(Converter(convert=converter, convert_path=k))
            make_converter(key, spec)

    ########################
    ###   CONFIG
    ########################

    def collect_configuration(self, configuration_file, args_dict):
        """Return us a MergedOptions with this configuration and any collected configurations"""
        errors = []

        configuration = self.start_configuration()

        configuration.update(
              { "getpass": getpass
              , "collector": self
              , "args_dict": args_dict
              }
            , source = "<preparation>"
            )

        sources = []
        if configuration_file:
            sources.append(configuration_file)

        home_dir_configuration = self.home_dir_configuration_location()
        if home_dir_configuration:
            sources.insert(0, home_dir_configuration)

        done = set()
        def add_configuration(src, prefix=None, extra=None):
            log.info("Adding configuration from %s", os.path.abspath(src))
            if os.path.abspath(src) in done:
                return
            else:
                done.add(os.path.abspath(src))

            if src is None or not os.path.exists(src):
                return

            try:
                if os.stat(src).st_size == 0:
                    result = VersionedDict({})
                else:
                    result = VersionedDict(self.read_file(src))
            except self.BadFileErrorKls as error:
                errors.append(error)
                return

            if not result:
                return

            if extra:
                result.update(extra)
            result["config_root"] = os.path.abspath(os.path.dirname(src))

            while prefix:
                part = prefix.pop()
                result = VersionedDict({part: result})

            self.add_configuration(configuration, add_configuration, done, result, src)

        for source in sources:
            add_configuration(source)

        self.extra_configuration_collection(configuration)

        if errors:
            raise self.BadConfigurationErrorKls("Some of the configuration was broken", _errors=errors)

        return configuration

