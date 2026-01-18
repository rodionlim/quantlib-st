"""
All default parameters that might be used in a system are stored here

Order of preferences is - passed in command line to calculation method,
                          stored in system config object
                          found in defaults

"""

from typing import Optional

import yaml

from quantlib_st.core.fileutils import resolve_path_and_filename_for_package

DEFAULT_FILENAME = "config.defaults.yaml"


def get_system_defaults_dict(filename: Optional[str] = None) -> dict:
    """
    >>> get_system_defaults_dict()['average_absolute_forecast']
    10.0
    """
    if filename is None:
        filename = DEFAULT_FILENAME
    default_file = resolve_path_and_filename_for_package(filename)
    with open(default_file) as file_to_parse:
        default_dict = yaml.load(file_to_parse, Loader=yaml.FullLoader)

    return default_dict


if __name__ == "__main__":
    import doctest

    doctest.testmod()
