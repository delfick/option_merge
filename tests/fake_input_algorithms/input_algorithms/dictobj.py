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
                assert sorted(val.keys()) == sorted(["specs", "addons"])
                specs = self.kls.specs.spec.normalise(Meta(val, []).at('specs'), val["specs"])
                addons = self.kls.addons.spec.normalise(Meta(val, []).at("addons"), val["addons"])
                return type("Result", (self.kls, ), {"specs": specs, "addons": addons})()
        FieldSpec = FieldSpecProperty(FieldSpec)

    class Field(object):
        def __init__(self, spec, wrapper=None):
            self.spec = spec
            if callable(self.spec):
                self.spec = self.spec()
            self.wrapper = wrapper
            if wrapper is not None:
                self.spec = wrapper(self.spec)

