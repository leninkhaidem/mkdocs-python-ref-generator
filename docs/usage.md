# Usage

A sample plugin configuration looks like this.

```yaml title="mkdocs.yml"
site_name: mkdocs-py-ref-gen
theme:
  name: material

plugins:
  - search
  - mkdocstrings
  - py-ref-gen:
      modules:
        - name: "my_module"
          exclude_dirs:
            - "some/dir/within/my_module"
          exclude-files:
            - "some_file.py"
            - "another/file.py"
          options:          # these options are mkdocstring python options
            key: value
  - literate-nav:
      nav_file: SUMMARY.md
  - section-index
nav:
  - Home: index.md
  - API Reference: reference/
```

## How does it work ?

The plugin uses [mkdocs-gen-file](https://github.com/oprypin/) and [mkdocs-literate-nav](https://github.com/oprypin/mkdocs-literate-nav) to generate corresponding markdown files containing reference md files by following the recipe detailed [here](https://mkdocstrings.github.io/recipes/)

For a package having the following structure

```console title="Python package"
my_test_package
├── __init__.py
├── module_a.py
├── test_pkg
│   ├── _private_mod.py
│   ├── mod_a.py
│   └── mod_b.py
└── test_pkg_exclude
    ├── mod_a.py
```

Generated markdown reference files are as follows

```console title="Generated reference files"
docs/reference
├── SUMMARY.md
└── my_test_package
    ├── module_a.md
    ├── test_pkg
    │   ├── mod_a.md
    │   └── mod_b.md
    └── test_pkg_exclude
        ├── mod_a.md
        └── mod_b.md
```

!!! Note
    The plugin does not generate module reference for files starting with _ as they are treated as private modules.

## Sample generated reference file

```md
$ cat docs/reference/my_test_package/module_a.md

::: my_test_package.module_a
    handler: python
    options:
      show_root_heading: false
      allow_inspection: false
      show_root_full_path: true
      find_stubs_package: true
      show_source: false
      show_submodules: false
      members_order: source
      inherited_members: false
      summary:
        attributes: true
        methods: true
        classes: true
        modules: false
      imported_members: true
      docstring_section_style: spacy
      relative_crossrefs: true
      show_root_members_full_path: false
      show_object_full_path: false
      annotations_path: source
      show_category_heading: true
      group_by_category: true
      show_signature_annotations: true
      separate_signature: true
      signature_crossrefs: true
```

## Sample summary files

```md
$ cat docs/reference/SUMMARY.md

* my_test_package
    * [module_a](my_test_package/module_a.md)
    * test_pkg
        * [mod_a](my_test_package/test_pkg/mod_a.md)
        * [mod_b](my_test_package/test_pkg/mod_b.md)
    * test_pkg_exclude
        * [mod_a](my_test_package/test_pkg_exclude/mod_a.md)
        * [mod_b](my_test_package/test_pkg_exclude/mod_b.md)
```

## Configuration options

- `name`: The name of the python module. It should exist in the python path. Works if loaded through mkdocstrings python path option mentioned [here](https://mkdocstrings.github.io/python/usage/#paths)
- `exclude_dirs`: Path substring or folder name. The plugin skips generation of the content from these folders if any.
- `exclude_files`: Path substring or file names to be excluded
- `option`: This is the mkdocstring[python] configuration option documented [here](https://mkdocstrings.github.io/python/usage/#configuration). The plugin uses some default optinos as shown [here](#sample-generated-reference-file). This options are applied locally to all the generated files.

!!! Warning
    Local options overrides  global mkdocstring python options if specified. It's advised to use the python options under this plugin

## Command line utility

`py-ref-gen` command line utility can be used to generate the files if further customization is needed.

```shell title="py-ref-gen utility"
Usage: py-ref-gen [OPTIONS]

Options:
  --version                  Show the version and exit.
  -p, --path TEXT            Path to the module
  -n, --name TEXT            Name of the module  [required]
  -ef, --exclude-files TEXT  Files to exclude
  -ed, --exclude-dirs TEXT   Directories to exclude
  --help                     Show this message and exit.
```

This must be executed from the root folder where mkdocs.yml is located. Generated files will be saved under docs/reference.
