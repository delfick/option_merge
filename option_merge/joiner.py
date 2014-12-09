"""
Helpers for joining together things
"""

import six

def dot_joiner(*lsts):
    """Join lists of list of strings with a single dot in between each"""
    if len(lsts) == 1:
        return dot_joiner_path(lsts[0])
    elif len(lsts) == 2:
        return "{0}.{1}".format(dot_joiner_path(lsts[0]), dot_joiner_path(lsts[1]))
    else:
        return '.'.join(dot_joiner_path(lst) for lst in lsts)

def dot_joiner_path(lst):
    """Join list of strings with a single dot in between each"""
    result = []
    if hasattr(lst, "joined"):
        return lst.joined()

    if type(lst) in six.string_types:
        return lst

    if not type(lst) in (list, tuple):
        return str(lst)

    for part in lst:
        if hasattr(part, "joined"):
            part = part.joined()
        else:
            if type(part) in (list, tuple):
                part = ''.join(part)

            while part and part.startswith("."):
                part = part[1:]

            while part and part.endswith("."):
                part = part[:-1]

        if part:
            result.append(part)

    return '.'.join(str(res) for res in result)

def join(one, two):
    """
    Join two paths together

    Where either path is either string, list of strings or Path
    """
    if not two:
        return one
    if not one:
        return two

    from option_merge.path import Path
    if isinstance(one, Path):
        one = one.path
    if isinstance(two, Path):
        two = two.path

    if isinstance(one, six.string_types):
        if isinstance(two, six.string_types):
            return [one] + [two]
        else:
            return [one] + two
    else:
        if isinstance(two, six.string_types):
            return one + [two]
        else:
            return one + two

