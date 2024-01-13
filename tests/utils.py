import contextlib
import functools
import os.path
import shlex
import shutil
import subprocess

from ellar.common.utils.importer import get_main_directory_by_stack

SAMPLE_DUMB_DIRS = get_main_directory_by_stack("__main__/dumbs/", stack_level=1)
SAMPLE_DIRS = get_main_directory_by_stack(
    "__main__/test_migrations/samples", stack_level=1
)


def run_command(cmd, **kwargs):
    os.chdir(SAMPLE_DIRS)

    kwargs.setdefault("stdout", subprocess.PIPE)
    kwargs.setdefault("stderr", subprocess.PIPE)

    args = shlex.split(f"python {cmd}")
    return subprocess.run(args, **kwargs)


def clean_directory(directory):
    def _decorator(f):
        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            try:
                f(*args, **kwargs)
            finally:
                try:
                    shutil.rmtree(os.path.join(SAMPLE_DUMB_DIRS, directory))
                except OSError:
                    pass

        return _wrapper

    return _decorator


@contextlib.contextmanager
def set_env_variable(key, value):
    old_environ = dict(os.environ)
    os.environ[key] = value
    yield
    os.environ.clear()
    os.environ.update(old_environ)
