"""Command line options."""

import argparse
import sys
import toml
import json
import os

default_config_toml = ""

with open(os.path.join(os.path.dirname(__file__), 'config.toml'), 'r') as f:
    default_config_toml = f.read()


class Opts:
    """Parse command line options."""

    def __init__(self):
        """Parse and initialize the options."""
        parser = argparse.ArgumentParser(description='Management tool for '
                                         'DragonMint/Innosilicon miners.',
                                         formatter_class=argparse.
                                         ArgumentDefaultsHelpFormatter)

        parser.add_argument('-c', '--config', type=str,
                            help='Path to config file in either TOML or JSON format.',
                            default="config.toml")
        parser.add_argument('--print-config-toml', action='store_true',
                            help="Print default config in TOML and exit")
        parser.add_argument('--print-config-json', action='store_true',
                            help="Print default config in JSON and exit")

        self.args = parser.parse_args()

        if self.args.print_config_toml:
            print(default_config_toml)
            sys.exit(0)

        if self.args.print_config_json:
            print(json.dumps(toml.loads(default_config_toml),
                             sort_keys=True, indent=2))
            sys.exit(0)
