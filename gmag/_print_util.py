def verbose_print(verbose, *args, **kwargs):
    """Print if verbose is True

    :param verbose: verbose flag
    :param args: arguments to print
    :param kwargs: keyword arguments to print
    """

    if verbose:
        print(*args, **kwargs)


def red(string):
    """Return string in red

    :param string: string to return in red

    :return: string in red
    """

    return "\033[91m{}\033[00m".format(string)


def blue(string):
    """Return string in blue

    :param string: string to return in blue

    :return: string in blue
    """

    return "\033[94m{}\033[00m".format(string)


def bold(string):
    """Return string in bold

    :param string: string to return in bold

    :return: string in bold
    """

    return "\033[1m{}\033[00m".format(string)
