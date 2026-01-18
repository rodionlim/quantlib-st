import os
import glob
from importlib import import_module
from pathlib import Path
from typing import List, Tuple, Optional

## something unlikely to occur naturally in a pathname
RESERVED_CHARACTERS = "&!*"

"""
FILENAME RESOLUTION
"""


def resolve_path_and_filename_for_package(
    path_and_filename: str, separate_filename: Optional[str] = None
) -> str:
    """
    A way of resolving relative and absolute filenames, and dealing with awkward OS specific things

    >>> resolve_path_and_filename_for_package("/home/rodion/", "file.csv")
    '/home/rodion/file.csv'

    >>> resolve_path_and_filename_for_package(".home.rodion", "file.csv")
    '/home/rodion/file.csv'

    >>> resolve_path_and_filename_for_package("core.tests", "file.csv")
    '/home/rodion/quantlib_st/core/tests/file.csv'

    >>> resolve_path_and_filename_for_package("core.tests.file.csv")
    '/home/rodion/quantlib_st/core/tests/file.csv'

    """
    path_as_list = transform_path_into_list(path_and_filename)
    if separate_filename is None:
        path_as_list, separate_filename = (
            extract_filename_from_combined_path_and_filename_list(path_as_list)
        )

    resolved_pathname = get_pathname_from_list(path_as_list)

    # Use Path for clean joining
    return str(Path(resolved_pathname) / separate_filename)


def transform_path_into_list(pathname: str) -> List[str]:
    """
    Splits the pathname by '.', '/', and '\'.
    Matches the original implementation's behavior for absolute and relative paths.
    """
    # Normalize separators and split
    # Leading / or . will resulting in a leading empty string in the list
    normalized = pathname.replace(".", "/").replace("\\", "/")
    path_as_list = normalized.split("/")

    # The original implementation used rsplit and popped a trailing empty string
    if path_as_list and path_as_list[-1] == "" and len(path_as_list) > 1:
        path_as_list.pop()

    return path_as_list


def add_reserved_characters_to_pathname(pathname: str) -> str:
    """
    Kept for backward compatibility.
    """
    return (
        pathname.replace(".", RESERVED_CHARACTERS)
        .replace("/", RESERVED_CHARACTERS)
        .replace("\\", RESERVED_CHARACTERS)
    )


def extract_filename_from_combined_path_and_filename_list(
    path_and_filename_as_list: List[str],
) -> Tuple[List[str], str]:
    """
    Splits out the filename and extension from the end of the list.
    """
    extension = path_and_filename_as_list.pop()
    filename = path_and_filename_as_list.pop()

    separate_filename = f"{filename}.{extension}"
    return path_and_filename_as_list, separate_filename


def get_pathname_from_list(path_as_list: List[str]) -> str:
    """
    Determines if the path is absolute (Linux/Windows) or relative/package-based.
    """
    if not path_as_list:
        return "."

    first_part = path_as_list[0]

    if first_part == "":
        # path_type_absolute Linux (or start with dot)
        return get_absolute_linux_pathname_from_list(path_as_list[1:])
    elif is_window_path_list(path_as_list):
        # windoze absolute
        return get_absolute_windows_pathname_from_list(path_as_list)
    else:
        # package or standard relative
        return get_relative_pathname_from_list(path_as_list)


def get_absolute_linux_pathname_from_list(path_as_list: List[str]) -> str:
    """
    Returns the absolute linux pathname from a list
    """
    return os.path.sep + os.path.join(*path_as_list) if path_as_list else os.path.sep


def get_absolute_windows_pathname_from_list(path_as_list: List[str]) -> str:
    """
    Returns the absolute windows pathname from a list
    """
    drive_part = path_as_list[0]
    if drive_part.endswith(":"):
        # Ensure 'C:' becomes 'C:\' or 'C:/' depending on OS
        drive_part += os.path.sep

    return os.path.join(drive_part, *path_as_list[1:])


def get_relative_pathname_from_list(path_as_list: List[str]) -> str:
    """
    Resolves the path starting with a package name component.
    """
    if not path_as_list:
        return "."

    package_name = path_as_list[0]
    try:
        module = import_module(package_name)
        if hasattr(module, "__file__") and module.__file__:
            directory_name_of_package = os.path.dirname(module.__file__)
            return os.path.join(directory_name_of_package, *path_as_list[1:])
    except (ImportError, TypeError):
        # Fallback to current directory join if it's not a package
        pass

    return os.path.join(*path_as_list)


def is_window_path_list(path_as_list: List[str]) -> bool:
    """
    Checks if the path is a Windows-style drive path.
    """
    return bool(path_as_list and path_as_list[0].endswith(":"))


def does_filename_exist(filename: str) -> bool:
    resolved_filename = resolve_path_and_filename_for_package(filename)
    file_exists = does_resolved_filename_exist(resolved_filename)
    return file_exists


def does_resolved_filename_exist(resolved_filename: str) -> bool:
    file_exists = os.path.isfile(resolved_filename)
    return file_exists


def get_resolved_pathname(pathname: str) -> str:
    """
    Resolve a pathname that may be absolute or package-relative.
    """
    path_as_list = transform_path_into_list(pathname)
    return get_pathname_from_list(path_as_list)


def files_with_extension_in_pathname(
    pathname: str, extension: str = ".csv"
) -> List[str]:
    """
    Find all the files with a particular extension in a directory.
    """
    resolved_pathname = get_resolved_pathname(pathname)
    return files_with_extension_in_resolved_pathname(
        resolved_pathname, extension=extension
    )


def files_with_extension_in_resolved_pathname(
    resolved_pathname: str, extension: str = ".csv"
) -> List[str]:
    """
    Find all the files with a particular extension in a resolved directory.
    """
    file_list = [
        os.path.basename(f) for f in glob.glob(f"{resolved_pathname}/*{extension}")
    ]
    file_list_no_extension = [filename.split(".")[0] for filename in file_list]

    return file_list_no_extension
