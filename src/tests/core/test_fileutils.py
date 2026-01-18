import os

from quantlib_st.core.fileutils import (
    resolve_path_and_filename_for_package,
    transform_path_into_list,
    extract_filename_from_combined_path_and_filename_list,
    get_pathname_from_list,
    is_window_path_list,
)


def test_transform_path_into_list():
    assert transform_path_into_list("/home/user/file.csv") == [
        "",
        "home",
        "user",
        "file",
        "csv",
    ]
    assert transform_path_into_list("C:\\Data\\test.txt") == [
        "C:",
        "Data",
        "test",
        "txt",
    ]
    assert transform_path_into_list("package.sub.module") == [
        "package",
        "sub",
        "module",
    ]
    # Trailing slash should be popped if there are other elements
    assert transform_path_into_list("/home/user/") == ["", "home", "user"]
    # Only a slash should remain as ["", ""] or similar?
    # Actually split("/") on "/" gives ["", ""]
    # The logic says: if len > 1 and last is "" pop.
    # So "/" -> ["", ""] -> [""]
    assert transform_path_into_list("/") == [""]


def test_extract_filename():
    path_list = ["home", "user", "data", "csv"]
    p, f = extract_filename_from_combined_path_and_filename_list(path_list)
    assert p == ["home", "user"]
    assert f == "data.csv"


def test_is_window_path():
    assert is_window_path_list(["C:", "Users"]) is True
    assert is_window_path_list(["", "home"]) is False
    assert is_window_path_list(["package"]) is False


def test_get_pathname_from_list_linux(monkeypatch):
    # Test absolute Linux path
    # get_pathname_from_list(["", "home", "user"]) -> "/home/user"
    path = get_pathname_from_list(["", "home", "user"])
    # On non-windows it should use /
    if os.name != "nt":
        assert path == "/home/user"


def test_get_pathname_from_list_windows():
    # Test Windows path
    path = get_pathname_from_list(["C:", "Data"])
    # it should handle C:\Data
    assert "C:" in path
    assert "Data" in path


def test_resolve_path_and_filename_smoke():
    # Smoke test for resolve_path_and_filename_for_package
    # Absolute path
    res = resolve_path_and_filename_for_package("/tmp/test", "file.txt")
    assert "test" in res
    assert "file.txt" in res

    # Combined path
    res = resolve_path_and_filename_for_package("/tmp/test/file.txt")
    assert "test" in res
    assert "file.txt" in res


def test_package_resolution():
    # Test resolution of an actual package in the workspace
    # Need to make sure PYTHONPATH includes quantlib/src
    res = resolve_path_and_filename_for_package("quantlib_st.core", "fileutils.py")
    assert "quantlib_st" in res
    assert "core" in res
    assert "fileutils.py" in res
    assert os.path.exists(res)
