import dataclasses
import functools
import logging
import os
import pathlib
import pkgutil
import typing

import mkdocs_gen_files

log = logging.getLogger(f"mkdocs.plugins.{__name__}")


def get_module_path(module_name: str) -> str:
    if not module_name:
        raise ValueError("module_name is required")
    info = pkgutil.find_loader(module_name)
    if not info:
        raise ImportError(f"module {module_name} not found")
    return pathlib.Path(info.get_filename()).parent.parent.as_posix()


def dict_to_yaml(data, indent=0):
    """
    Convert a dictionary to a YAML formatted string.

    Args:
        data (dict): The dictionary to convert.
        indent (int): The indentation level (default is 0).

    Returns:
        str: The YAML formatted string.

    Example:
        >>> dict_to_yaml({'key': 'value'})
        'key: value\n'
    """
    yaml_str = ""
    for key, value in data.items():
        yaml_str += "  " * indent + str(key) + ":"
        if isinstance(value, dict):
            yaml_str += "\n" + dict_to_yaml(value, indent + 1)
        elif isinstance(value, bool):
            yaml_str += " " + ("true" if value else "false") + "\n"
        else:
            yaml_str += f" {str(value)}" + "\n"
    return yaml_str


def get_options_str(options: typing.Optional[dict] = None) -> str:
    """
    Get the options as a YAML formatted string.

    Args:
        options (dict, optional): The options dictionary. Defaults to None.

    Returns:
        str: The options as a YAML formatted string.

    Example:
        >>> get_options_str({'show_root_heading': 'true'})
        '   show_root_heading: true\n   allow_inspection: false\n...'
    """
    defaults = {
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
    }
    options = {**defaults, **(options or {})}
    return dict_to_yaml(options, indent=3)


def get_md_content(identifier: str, options: typing.Optional[dict] = None) -> str:
    """
    Get the markdown content for a given identifier.

    Args:
        identifier (str): The identifier for the module/class/function.
        options (dict, optional): The options dictionary. Defaults to None.

    Returns:
        str: The markdown content.

    Example:
        >>> get_md_content('os.path')
        '\\n::: os.path\\n    handler: python\\n    options:\\n   show_root_heading: false\\n...'
    """
    return f"""
::: {identifier}
    handler: python
    options:
{get_options_str(options)}
"""


@dataclasses.dataclass
class Module:
    name: str
    path: str
    exclude_files: typing.List[str]
    exclude_dirs: typing.List[str]
    options: dict


def _normalize_paths(paths: typing.List[str]) -> typing.List[str]:
    """
    Normalize a list of file paths to POSIX format.

    Args:
        paths (list): The list of file paths.

    Returns:
        list: The normalized list of file paths.

    Example:
        >>> _normalize_paths(['C:\\path\\to\\file'])
        ['C:/path/to/file']
    """
    return [pathlib.Path(_x).as_posix() for _x in paths if _x]


def _should_exclude(path: pathlib.Path, exclude_files: typing.List[str], exclude_dirs: typing.List[str]) -> bool:
    """
    Determine if a file should be excluded based on the exclusion lists.

    Args:
        path (pathlib.Path): The file path.
        exclude_files (list): The list of files to exclude.
        exclude_dirs (list): The list of directories to exclude.

    Returns:
        bool: True if the file should be excluded, False otherwise.

    Example:
        >>> _should_exclude(pathlib.Path('test.py'), ['test.py'], [])
        True
    """
    if os.path.basename(path).startswith("_"):
        return True
    exclude_files = _normalize_paths(exclude_files)
    exclude_dirs = _normalize_paths(exclude_dirs)
    if any(path.absolute().as_posix().endswith(_x) for _x in exclude_files):
        return True
    dir_name = os.path.dirname(path)
    return any(dir_name.endswith(_x) for _x in exclude_dirs)


def render_ref(module: Module,
               nav: mkdocs_gen_files.nav.Nav) -> mkdocs_gen_files.nav.Nav:
    """
    Render the reference documentation for a module.

    Args:
        module (Module): The module to document.
        nav (mkdocs_gen_files.nav.Nav): The navigation object.

    Returns:
        mkdocs_gen_files.nav.Nav: The updated navigation object.

    Example:
        >>> module = Module(name='os', path='/usr/lib/python3.9', exclude_files=[], exclude_dirs=[], options={})
        >>> nav = mkdocs_gen_files.nav.Nav()
        >>> render_ref(module, nav)
        <mkdocs_gen_files.nav.Nav object at 0x...>
    """
    for path in sorted(pathlib.Path(module.path, module.name).rglob("*.py")):
        if _should_exclude(path, module.exclude_files, module.exclude_dirs):
            continue
        module_path = path.relative_to(module.path).with_suffix("")
        doc_path = path.relative_to(module.path).with_suffix(".md")
        full_doc_path = pathlib.Path("reference", doc_path)
        parts = tuple(module_path.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")
        elif parts[-1] == "__main__":
            continue
        nav[parts] = doc_path.as_posix()
        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            identifier = ".".join(parts)
            md_content = get_md_content(identifier, options=module.options)
            print(f"{md_content}", file=fd)
    return nav


def generate_summary(nav: mkdocs_gen_files.nav.Nav):
    """
    Generate the SUMMARY.md file for the documentation.

    Args:
        nav (mkdocs_gen_files.nav.Nav): The navigation object.

    Example:
        >>> nav = mkdocs_gen_files.nav.Nav()
        >>> generate_summary(nav)
    """
    path = pathlib.Path("reference", "SUMMARY.md")
    with mkdocs_gen_files.open(path.as_posix(), "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


@functools.lru_cache
def get_root_path() -> pathlib.Path:
    """
    Get the root path of the project.

    Returns:
        pathlib.Path: The root path of the project.

    Example:
        >>> get_root_path()
        PosixPath('/Users/khaising/Documents/git-repositories/mkdocs-python-ref-generator')
    """
    return pathlib.Path(__file__).parent.parent
