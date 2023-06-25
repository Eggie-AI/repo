import os
import pathlib
import shutil


def assert_empty(path: pathlib.Path, clean: bool, type = 'folder'):
    if os.path.exists(path):
        if not clean:
            print(f"Output {type} '{path}' already exists (use --clean to overwrite)")
            exit(1)
        else:
            if type == 'folder':
                shutil.rmtree(path)
            elif type == 'file':
                os.remove(path)
    else:
        if type == 'folder':
            os.makedirs(path)
        elif type == 'file':
            os.makedirs(path.parent, exist_ok=True)
