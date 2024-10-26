import hashlib
import os
import pathlib
import shutil
from unittest.mock import MagicMock

import mkdocs_gen_files
import pytest

from mkdocs_py_ref_gen.generator import (Module, dict_to_yaml,
                                         generate_summary, get_md_content,
                                         get_module_path, get_options_str,
                                         render_ref, should_exclude)


def test_get_module_path_valid():
    assert get_module_path("os") == pathlib.Path(
        os.__file__).parent.parent.as_posix()


def test_get_module_path_invalid():
    with pytest.raises(ImportError):
        get_module_path("non_existent_module")


def test_get_module_path_empty():
    with pytest.raises(ValueError):
        get_module_path("")


def test_dict_to_yaml_simple():
    data = {'key': 'value'}
    expected = 'key: value\n'
    assert dict_to_yaml(data) == expected


def test_dict_to_yaml_nested():
    data = {'key': {'nested_key': 'nested_value'}}
    expected = 'key:\n  nested_key: nested_value\n'
    assert dict_to_yaml(data) == expected


def test_dict_to_yaml_boolean():
    data = {'key': True}
    expected = 'key: true\n'
    assert dict_to_yaml(data) == expected


def test_get_options_str_default():
    expected = dict_to_yaml({
        "show_root_heading": "false",
        "allow_inspection": "false",
        "show_root_full_path": "true",
        "find_stubs_package": "true",
        "show_source": "false",
        "show_submodules": "false",
        "members_order": "source",
        "inherited_members": "false",
        "summary": {
            "attributes": True,
            "methods": True,
            "classes": True,
            "modules": False
        },
        "imported_members": "true",
        "docstring_section_style": "spacy",
        "relative_crossrefs": "true",
        "show_root_members_full_path": "false",
        "show_object_full_path": "false",
        "annotations_path": "source",
        "show_category_heading": "true",
        "group_by_category": "true",
        "show_signature_annotations": "true",
        "separate_signature": "true",
        "signature_crossrefs": "true"
    }, indent=3)
    assert get_options_str() == expected


def test_get_options_str_custom():
    options = {'show_root_heading': 'true'}
    expected = dict_to_yaml({
        "show_root_heading": "true",
        "allow_inspection": "false",
        "show_root_full_path": "true",
        "find_stubs_package": "true",
        "show_source": "false",
        "show_submodules": "false",
        "members_order": "source",
        "inherited_members": "false",
        "summary": {
            "attributes": True,
            "methods": True,
            "classes": True,
            "modules": False
        },
        "imported_members": "true",
        "docstring_section_style": "spacy",
        "relative_crossrefs": "true",
        "show_root_members_full_path": "false",
        "show_object_full_path": "false",
        "annotations_path": "source",
        "show_category_heading": "true",
        "group_by_category": "true",
        "show_signature_annotations": "true",
        "separate_signature": "true",
        "signature_crossrefs": "true"
    }, indent=3)
    assert get_options_str(options) == expected


def test_get_md_content_default():
    identifier = 'os.path'
    expected = f"""
::: {identifier}
    handler: python
    options:
{get_options_str()}
"""
    assert get_md_content(identifier) == expected


def test_get_md_content_custom():
    identifier = 'os.path'
    options = {'show_root_heading': 'true'}
    expected = f"""
::: {identifier}
    handler: python
    options:
{get_options_str(options)}
"""
    assert get_md_content(identifier, options) == expected


def test_should_exclude_file():
    path = pathlib.Path('test.py')
    exclude_files = ['test.py']
    exclude_dirs = []
    assert should_exclude(path, exclude_files, exclude_dirs) is True


def test_should_exclude_dir():
    path = pathlib.Path('dir/test.py')
    exclude_files = []
    exclude_dirs = ['dir']
    assert should_exclude(path, exclude_files, exclude_dirs) is True


def test_should_not_exclude():
    path = pathlib.Path('test.py')
    exclude_files = []
    exclude_dirs = []
    assert should_exclude(path, exclude_files, exclude_dirs) is False


def delete_ref_folder():
    folder = os.path.join("docs", "reference")
    if os.path.exists(folder):
        shutil.rmtree(folder)


def get_generated_md_files(path):
    return sorted([_x.relative_to("docs").as_posix() for _x in pathlib.Path(path).rglob("*.md")])


def test_render_ref():
    module = Module(name='my_test_package', path="tests",
                    exclude_files=[], exclude_dirs=[], options={})
    delete_ref_folder()
    nav = mkdocs_gen_files.nav.Nav()
    files = sorted(render_ref(module, nav))
    print(len(files))
    assert files == get_generated_md_files(
        "docs/reference") and len(files) == 5


def compute_sha512_hash(string: str):
    """
    Computes the SHA-512 hash of a given string and returns the first 32 characters of the hexadecimal digest.

    Args:
        string (str): The input string to be hashed.

    Returns:
        str: The first 32 characters of the SHA-512 hexadecimal digest of the input string.
    """
    sha_hash = hashlib.sha512()
    sha_hash.update(string.encode('utf-8'))
    return sha_hash.hexdigest()[:32]


def test_generate_summary():
    module = Module(name='my_test_package', path="tests",
                    exclude_files=[], exclude_dirs=["test_pkg_exclude"], options={})
    delete_ref_folder()
    nav = mkdocs_gen_files.nav.Nav()
    render_ref(module, nav)
    generate_summary(nav)
    with open(pathlib.Path("docs", "reference", "SUMMARY.md")) as fd:
        assert compute_sha512_hash(
            fd.read()) == "f6fc7e08ff8aefe481f08388408357ac"


# test_render_ref()
