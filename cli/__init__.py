#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

"""
An installer for Foreman.
"""
import os
import obsah
import sys
from importlib import resources


class ApplicationConfig(obsah.ApplicationConfig):
    """
    A class describing the where to find various files
    """

    @staticmethod
    def name():
        """
        Return the name as shown to the user in the ArgumentParser
        """
        return 'rop'

    @staticmethod
    def data_path():
        path = os.environ.get('ROP_DATA')
        if path is None:
            with resources.path(__name__, 'data') as fspath:
                path = fspath.as_posix()

        return path

    @staticmethod
    def inventory_path():
        """
        Return the inventory path
        """
        return os.environ.get('ROP_INVENTORY', os.path.join(os.getcwd(), 'inventories'))


def main(cliargs=None, application_config=ApplicationConfig):  # pylint: disable=R0914
    """
    Main command
    """
    obsah.main(cliargs=cliargs, application_config=application_config)


if __name__ == '__main__':
    main()
