import logging
import tempfile
import typing

import mkdocs_gen_files
from mkdocs.config import Config, base
from mkdocs.config import config_options as c
from mkdocs.structure.files import Files
from mkdocs_gen_files.editor import FilesEditor
from mkdocs_gen_files.plugin import GenFilesPlugin

from . import generator

log = logging.getLogger(f"mkdocs.plugins.{__name__}")

try:
    from mkdocs.exceptions import PluginError
except ImportError:
    PluginError = SystemExit  # type: ignore


class ModuleConfig(base.Config):
    name = c.Type(str)
    path = c.Type(str, default="")
    exclude_files = c.Type(list, default=[])
    exclude_dirs = c.Type(list, default=[])
    options = c.Type(dict, default={})


class PluginConfig(base.Config):
    modules = c.ListOfItems(c.SubConfig(ModuleConfig), default=[])


class MkDocsPyRefGenPlugin(GenFilesPlugin):
    config_scheme = (('modules', c.ListOfItems(
        c.SubConfig(ModuleConfig), default=[])),)

    def _get_modules(self) -> typing.List[generator.Module]:
        modules = [
            generator.Module(name=_x['name'],
                             path=_x['path'] or generator.get_module_path(
                                 _x['name']),
                             exclude_files=_x.get("exclude_files", []),
                             exclude_dirs=_x.get("exclude_dirs", []),
                             options=_x.get("options", {}))
            for _x in self.config['modules']
        ]
        if not modules:
            raise PluginError("No modules specified for py-ref-gen plugin")
        return modules

    def on_files(self, files: Files, config: Config) -> Files:
        self._dir = tempfile.TemporaryDirectory(prefix="mkdocs_gen_files_")
        modules = self._get_modules()
        with FilesEditor(files, config, self._dir.name) as ed:
            nav = mkdocs_gen_files.Nav()
            for module in modules:
                generator.render_ref(module, nav)
            generator.generate_summary(nav)
        self._edit_paths = dict(ed.edit_paths)
        return ed.files
