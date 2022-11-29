def verbose_print(verbose, *args, **kwargs):
    """Print if verbose is True

    Parameters
    ----------
    verbose : `bool`
        If True, print the message
    *args
        Arguments to pass to print
    **kwargs
        Keyword arguments to pass to print
    """

    if verbose:
        print(*args, **kwargs)


def red(string):
    """Return string in red

    Parameters
    ----------
    string : `str`
        String to return in red

    Returns
    -------
    str
        String in red
    """

    return "\033[91m{}\033[00m".format(string)


def blue(string):
    """Return string in blue

    Parameters
    ----------
    string : `str`
        String to return in blue

    Returns
    -------
    str
        String in blue
    """

    return "\033[94m{}\033[00m".format(string)


def bold(string):
    """Return string in bold

    Parameters
    ----------
    string : `str`
        String to return in bold

    Returns
    -------
    str
        String in bold
    """

    return "\033[1m{}\033[00m".format(string)
