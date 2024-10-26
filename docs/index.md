# mkdocs-py-ref-gen

mkdocs plugin to generate reference mdfiles and summary of python package(s)

It's a wrapper plugin built using [mkdocs-gen-file](https://github.com/oprypin/) and [mkdocs-literate-nav](https://github.com/oprypin/mkdocs-literate-nav)

<!-- termynal -->
```console
$ pip install mkdocs-py-ref-gen
```

The plugin requires [mkdocstrings[python]](https://mkdocstrings.github.io/python)

```shell
pip install 'mkdocstrings[python]'
```


## usage

```yaml title="plugin config"
plugins:
  - py-ref-gen:
      modules:
        - name: "my_module"

```