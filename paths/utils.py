def base36encode(num):
    """Converts a positive integer into a base36 string."""

    if not isinstance(num, int):
        raise TypeError("Positive integer must be provided for base36encode. " + repr(num) + " provided instead.")

    if not num >= 0:
        raise ValueError('Negative integers are not permitted for base36encode.')

    digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    res = ''
    while not res or num > 0:
        num, i = divmod(num, 36)
        res = digits[i] + res
    return res


def base36decode(base36_string):
    """Converts base36 string into integer."""
    return int(base36_string, 36)


def xstr(s):
    if s is None:
        return ''
    else:
        return str(s)