import six

class BadSpecValue(Exception): pass

class NotSpecified(object):
    @classmethod
    def items(kls):
        return []

class Spec(object):
    def normalise(self, meta, val):
        raise NotImplementedError()

class defaulted(Spec):
    def __init__(self, spec, default):
        self.spec = spec
        self.default = default

    def normalise(self, meta, val):
        if val is NotSpecified:
            return self.default
        else:
            return self.spec.normalise(meta, val)

class any_spec(Spec):
    def normalise(self, meta, val):
        return val

class dictof(Spec):
    def __init__(self, name_spec, value_spec):
        self.name_spec = name_spec
        self.value_spec = value_spec

    def normalise(self, meta, val):
        result = {}
        for k, v in val.items():
            result[self.name_spec.normalise(meta.at(k), k)] = self.value_spec.normalise(meta.at(k), v)
        return result

class tuple_spec(Spec):
    def __init__(self, spec):
        self.spec = spec

    def normalise(self, meta, val):
        val = tuple(val)
        return tuple(self.spec.normalise(meta, v) for v in val)

class tupleof(Spec):
    def __init__(self, *specs):
        self.specs = specs

    def normalise(self, meta, val):
        val = tuple(val)
        if len(val) != len(self.specs):
            raise BadSpecValue("Wrong length")
        return tuple(self.specs[i].normalise(meta, val[i]) for i in range(len(self.specs)))

class integer_spec(Spec):
    def normalise(self, meta, val):
        return int(val)

class string_spec(Spec):
    def normalise(self, meta, val):
        if not isinstance(val, six.string_types):
            raise BadSpecValue("Expected a string\tGot={0}".format(val))
        return val

class has(Spec):
    def __init__(self, *properties):
        self.properties = properties

    def normalise(self, meta, val):
        for prop in self.properties:
            if not hasattr(val, prop):
                raise BadSpecValue("Expected a {0} property".format(prop))
        return val

class listof(Spec):
    def __init__(self, spec):
        self.spec = spec

    def normalise(self, meta, val):
        if val is NotSpecified:
            return []
        if type(val) is not list:
            val = []
        return [self.spec.normalise(meta, v) for v in val]
