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


def should_exclude(path: pathlib.Path, exclude_files: typing.List[str], exclude_dirs: typing.List[str]) -> bool:
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
    if any(path.absolute().as_posix().endswith(_x) for _x in exclude_files):
        return True
    dir_name = os.path.dirname(path)
    return any(dir_name.endswith(_x) for _x in exclude_dirs)


def render_ref(module: Module,
               nav: mkdocs_gen_files.nav.Nav) -> typing.List[str]:
    """
    Renders the reference documentation for a given module and updates the navigation.

    This function scans the specified module directory for Python files, generates
    corresponding Markdown documentation files, and updates the navigation structure
    for MkDocs.

    Args:
        module (Module): The module for which to generate reference documentation.
            - path (str): The path to the module directory.
            - name (str): The name of the module.
            - exclude_files (list): List of files to exclude from documentation.
            - exclude_dirs (list): List of directories to exclude from documentation.
            - options (dict): Additional options for generating documentation.
        nav (mkdocs_gen_files.nav.Nav): The MkDocs navigation object to update.

    Returns:
        typing.List[str]: A list of paths to the generated Markdown documentation files.

    Example:
        module = Module(
            path="/path/to/module",
            name="module_name",
            exclude_files=["excluded_file.py"],
            exclude_dirs=["excluded_dir"],
            options={"option_key": "option_value"}
        )
        nav = mkdocs_gen_files.nav.Nav()
        files = render_ref(module, nav)
        print(files)
    """
    files = []
    for path in sorted(pathlib.Path(module.path, module.name).rglob("*.py")):
        if should_exclude(path, module.exclude_files, module.exclude_dirs):
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
        files.append(full_doc_path.as_posix())
        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            identifier = ".".join(parts)
            md_content = get_md_content(identifier, options=module.options)
            print(f"{md_content}", file=fd)
    return files


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
