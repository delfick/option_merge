from input_algorithms import spec_base as sb

def __option_merge__(configuration, result_maker, **kwargs):
    return result_maker(specs={(0, "two"): sb.integer_spec()}, addons=[])

