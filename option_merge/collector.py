"""
The collector object is responsible for collecting configuration
and setting up converters
"""

from option_merge.versioning import VersionedDict

from delfick_error import DelfickError
from getpass import getpass
import logging
import os

log = logging.getLogger("option_merge.collector")

class Collector(object):
    BadFileErrorKls = DelfickError
    BadConfigurationErrorKls = DelfickError

    ########################
    ###   HOOKS
    ########################

    def alter_clone_cli_args(self, new_collector, new_cli_args, *args, **kwargs):
        """Hook for altering cli_args given to a clone collector"""

    def find_missing_config(self, configuration):
        """Hook to raise errors about missing configuration"""

    def extra_prepare(self, configuration, cli_args):
        """Hook for any extra preparation before the converters are activated"""

    def extra_prepare_after_activation(self, configuration, cli_args):
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
        if not hasattr(self, "configuration_file"):
            return self.__class__()
        new_collector = self.__class__()
        new_cli_args = dict(self.configuration["cli_args"].items())
        self.alter_clone_cli_args(new_collector, new_cli_args, *args, **kwargs)
        new_collector.prepare(self.configuration_file, new_cli_args)
        return new_collector

    def prepare(self, configuration_file, cli_args):
        """Do the bespin stuff"""
        self.configuration_file = configuration_file
        self.configuration = self.collect_configuration(configuration_file)

        self.find_missing_config(self.configuration)

        self.configuration.update(
            { "getpass": getpass
            , "collector": self
            , "cli_args": cli_args
            }
        , source = "<preparation>"
        )

        self.extra_prepare(self.configuration, cli_args)
        self.configuration.converters.activate()
        self.extra_prepare_after_activation(self.configuration, cli_args)

    ########################
    ###   CONFIG
    ########################

    def collect_configuration(self, configuration_file):
        """Return us a MergedOptions with this configuration and any collected configurations"""
        errors = []

        configuration = self.start_configuration()

        sources = [configuration_file]
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

