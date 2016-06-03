def find_input_algorithms(package="input_algorithms", version=">=0.5"):
    try:
        __import__(package)
    except ImportError:
        raise Exception("To use option_merge addons your program must also have {0} as a requirement".format(package))

    import pkg_resources
    try:
        pkg_resources.working_set.require(["{0}{1}".format(package, version)])
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict) as error:
        raise Exception("Have invalid version of {0}\terror={1}".format(package, error))

find_input_algorithms()

from input_algorithms.dictobj import dictobj
from input_algorithms import spec_base as sb
from input_algorithms.meta import Meta

import pkg_resources
import logging

log = logging.getLogger("option_merge.addons")

class Result(dictobj.Spec):
    specs = dictobj.Field(lambda: sb.dictof(sb.tupleof(sb.integer_spec(), sb.tuple_spec(sb.string_spec())), sb.has("normalise")))
    addons = dictobj.Field(sb.string_spec, wrapper=sb.listof)

class Addon(object):
    class NoSuchAddon(Exception):
        _fake_delfick_error = True
        def __init__(self, addon):
            self.message = ""
            self.addon = addon
            self.kwargs = dict(addon=addon)
        def __str__(self):
            return "No Such addon\taddon={0}".format(self.addon)

    class BadImport(Exception):
        _fake_delfick_error = True
        def __init__(self, message, importing, module, error):
            self.message = message
            self.error = error
            self.module = module
            self.importing = importing
            self.kwargs = dict(importing=importing, module=module, error=error)
        def __str__(self):
            return "Bad import: {0}\timporting={1}\tmodule={2}\terror={3}".format(self.message, self.importing, self.module, self.error)

    class BadAddon(Exception):
        _fake_delfick_error = True
        def __init__(self, message, expected, got, addon):
            self.message = message
            self.got = got
            self.expected = expected
            self.addon = addon
            self.kwargs = dict(expected=expected, got=got, addon=addon)
        def __str__(self):
            return "Bad addon: {0}\texpected={1}\tgot={2}\taddon={3}".format(self.message, self.expected, self.got, self.addon)

    @classmethod
    def get(kls, entry_point_name, configuration, **kwargs):
        entry_points = list(pkg_resources.iter_entry_points("option_merge.addons", name=entry_point_name))
        if len(entry_points) > 1:
            log.warning("Found multiple entry_points for option_merge.addons.{0}".format(entry_point_name))
        elif len(entry_points) == 0:
            raise kls.NoSuchAddon(addon="option_merge.addons.{0}".format(entry_point_name))
        else:
            log.info("Found {0} addon".format(entry_point_name))

        def result_maker(**data):
            meta = Meta(data, [])
            return Result.FieldSpec().normalise(meta, data)

        for entry_point in entry_points:
            try:
                module = entry_point.resolve()
            except ImportError as error:
                raise kls.BadImport("Error whilst resolving entry_point", importing=entry_point_name, module=entry_point.module_name, error=str(error))

            if not hasattr(module, "__option_merge__"):
                raise kls.BadImport("Error after resolving entry_point", importing=entry_point_name, module=entry_point.module_name, error="Didn't find an __option_merge__ function")

            r = module.__option_merge__(configuration, result_maker, **kwargs)
            if not issubclass(r.__class__, Result):
                raise kls.BadAddon("Addon's __option_merge__ returned something wrong!", expected=Result, got=r.__class__, addon=entry_point_name)

            yield r

