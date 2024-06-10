import os

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar_cli.main import create_ellar_cli

if __name__ == "__main__":
    os.environ.setdefault(
        ELLAR_CONFIG_MODULE, "file_field_example.config:DevelopmentConfig"
    )

    # initialize Commandline program
    cli = create_ellar_cli("file_field_example.server:bootstrap")
    # start commandline execution
    cli(prog_name="Ellar Web Framework CLI")
