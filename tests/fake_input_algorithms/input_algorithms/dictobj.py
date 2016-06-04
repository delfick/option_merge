from input_algorithms.spec_base import NotSpecified, defaulted
from input_algorithms.meta import Meta

class FieldSpecProperty(object):
    def __init__(self, kls):
        self.kls = kls

    def __get__(self, obj, type=None):
        # Passing on Result so we can pretend we created a subclass of it lol
        self.kls.kls = type
        return self.kls

class dictobj(object):
    class Spec(object):
        class FieldSpec(object):
            def __init__(self, formatter=None):
                self.formatter = formatter

            def normalise(self, meta, val):
                specs = self.kls.specs.spec.normalise(Meta(val, []).at('specs'), val.get("specs", NotSpecified))
                addons = self.kls.addons.spec.normalise(Meta(val, []).at("addons"), val.get("addons", NotSpecified))
                post_register = self.kls.post_register.spec.normalise(Meta(val, []).at("post_register"), val.get("post_register", NotSpecified))
                return type("Result", (self.kls, ), {"specs": specs, "addons": addons, "post_register": post_register})()
        FieldSpec = FieldSpecProperty(FieldSpec)

    class Field(object):
        def __init__(self, spec, wrapper=None, default=NotSpecified):
            self.spec = spec
            if callable(self.spec):
                self.spec = self.spec()
            self.wrapper = wrapper
            if wrapper is not None:
                self.spec = wrapper(self.spec)
            if default is not NotSpecified:
                self.spec = defaulted(self.spec, default)

