import dataclasses
import functools
import os
import pathlib
import sys
import typing

import mkdocs_gen_files


def get_module_conf() -> typing.List[dict]:
    script_dir = pathlib.Path(__file__).parent.as_posix()
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    import module_conf
    return module_conf.modules


def dict_to_yaml(data, indent=0):
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
    exclusions: typing.List[str]
    options: dict


def get_modules() -> typing.List[Module]:
    return [
        Module(name=_x['name'],
               path=_x['path'],
               exclusions=_x.get("exclude-files", []),
               options=_x.get("options", {}))
        for _x in get_module_conf()
    ]


def render_ref(module: Module, nav: mkdocs_gen_files.Nav) -> mkdocs_gen_files.Nav:
    root_path = get_root_path()
    src = os.path.join(root_path, module.path)
    for path in sorted(pathlib.Path(src, module.name).rglob("*.py")):
        if any(path.absolute().as_posix().endswith(_x) for _x in module.exclusions):
            continue
        module_path = path.relative_to(src).with_suffix("")
        doc_path = path.relative_to(src).with_suffix(".md")
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
    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root_path))
    return nav


def generate_summary(nav: mkdocs_gen_files.Nav):
    with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


@functools.lru_cache
def get_root_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent


nav = mkdocs_gen_files.Nav()
for module in get_modules():
    render_ref(module, nav)
generate_summary(nav)
