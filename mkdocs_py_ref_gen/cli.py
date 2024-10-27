import os
import sys

import click
import mkdocs_gen_files

from . import __version__, generator

o = click.option


@click.command()
@click.version_option(version=__version__, prog_name=os.path.basename(sys.argv[0]))
@o("-p", "--path", help="Path to the module", default="")
@o("-n", "--name", help="Name of the module", required=True)
@o("-ef", "--exclude-files", help="Files to exclude", multiple=True)
@o("-ed", "--exclude-dirs", help="Directories to exclude", multiple=True)
def main(name: str, path: str, exclude_files: tuple[str], exclude_dirs: tuple[str]):
    nav = mkdocs_gen_files.nav.Nav()
    module = generator.Module(
        name=name,
        path=path or generator.get_module_path(name),
        exclude_files=list(exclude_files),
        exclude_dirs=list(exclude_dirs),
        options=True
    )

    generator.render_ref(module=module, nav=nav)
    generator.generate_summary(nav)
