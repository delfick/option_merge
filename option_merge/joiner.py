"""
Helpers for joining together things
"""

import six
list_types = (list, tuple)
string_types = (str, ) + six.string_types

def dot_joiner(item, item_type=None):
    """Join lists of list of strings with a single dot in between each"""
    if item:
        if item_type in string_types:
            return item
        else:
            return dot_join_item(item, item_type or type(item))
    else:
        return ""

def dot_join_item(item, item_type):
    """
    Join list of strings with a single dot in between each

    Note that if the items have dots in them, then it's possible to have multiple dots.

    This is fine, as long as we are consistent
    """
    result = []
    joined = getattr(item, "joined", None)
    if joined is not None:
        return joined()

    if item_type not in (list, tuple):
        return str(item)

    for part in item:
        part_type = type(part)
        if part_type not in string_types:
            joined = getattr(part, "joined", None)
            if joined is not None:
                part = joined()
                if part:
                    result.append(part)
                continue

        if part_type in list_types:
            part = ''.join(part)

        if part:
            result.append(part)

    return '.'.join(result)

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

