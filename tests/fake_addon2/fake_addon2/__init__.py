from input_algorithms import spec_base as sb

VERSION = "0.1"

def __option_merge__(configuration, result_maker, **kwargs):
    return result_maker(specs={(9, ("one", "two")): sb.integer_spec()}, addons=[])

