import sys
import tempfile
import typing

import mkdocs_gen_files
from mkdocs.config import Config, base
from mkdocs.config import config_options as c
from mkdocs.structure.files import Files
from mkdocs_gen_files.editor import FilesEditor
from mkdocs_gen_files.plugin import GenFilesPlugin

from . import generator

try:
    from mkdocs.exceptions import PluginError
except ImportError:
    PluginError = SystemExit  # type: ignore


def validate_options(value):
    if not isinstance(value, (dict, bool)):
        raise ValueError("options must be a dict or a bool")
    return value


class ModuleConfig(base.Config):
    name = c.Type(str)
    path = c.Type(str, default="")
    exclude_files = c.Type(list, default=[])
    exclude_dirs = c.Type(list, default=[])
    options = c.Type((dict, bool), default=True)


class PluginConfig(base.Config):
    modules = c.ListOfItems(c.SubConfig(ModuleConfig), default=[])


def safe_getattr(obj, attr, default=None):
    try:
        for part in attr.split('.'):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return default


class MkDocsPyRefGenPlugin(GenFilesPlugin):
    config_scheme = (('modules', c.ListOfItems(
        c.SubConfig(ModuleConfig), default=[])),)

    def _load_paths(self, config: Config):
        handlers = safe_getattr(
            config['plugins'].get('mkdocstrings'), 'config.handlers', {})
        python_handler = handlers.get('python', {})
        paths = python_handler.get('paths', [])
        for path in paths:
            if path in sys.path:
                continue
            sys.path.append(path)

    def on_config(self, config):
        self._load_paths(config)

    def _get_modules(self) -> typing.List[generator.Module]:
        modules = [
            generator.Module(name=_x['name'],
                             path=_x['path'] or generator.get_module_path(
                                 _x['name']),
                             exclude_files=_x.get("exclude_files", []),
                             exclude_dirs=_x.get("exclude_dirs", []),
                             options=_x.get("options", True))
            for _x in self.config['modules']
        ]
        if not modules:
            raise PluginError("No modules specified for py-ref-gen plugin")
        return modules

    def on_files(self, files: Files, config: Config) -> Files:
        self._dir = tempfile.TemporaryDirectory(prefix="mkdocs_gen_files_")
        modules = self._get_modules()
        with FilesEditor(files, config, self._dir.name) as ed:
            nav = mkdocs_gen_files.nav.Nav()
            for module in modules:
                generator.render_ref(module, nav)
            generator.generate_summary(nav)
        self._edit_paths = dict(ed.edit_paths)
        return ed.files
