"""
Helpers for joining together things
"""

import six

def dot_joiner(*lsts):
    """Join lists of list of strings with a single dot in between each"""
    return '.'.join(dot_joiner_path(lst) for lst in lsts)

def dot_joiner_path(lst):
    """Join list of strings with a single dot in between each"""
    result = []
    if isinstance(lst, six.string_types):
        return lst

    if not isinstance(lst, (list, tuple)):
        return unicode(lst)

    for part in lst:
        if isinstance(part, (list, tuple)):
            part = ''.join(part)

        while part and part.startswith("."):
            part = part[1:]

        while part and part.endswith("."):
            part = part[:-1]

        if part:
            result.append(part)

    return '.'.join(unicode(res) for res in result)

def join(one, two):
    """
    Join two paths together

    Where either path is either string, list of strings or Path
    """
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

