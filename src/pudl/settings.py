"""
This module opens the YAML configuration file.

Whenever using any of the settings in the configuration file in a module,
import this module as `from config import settings`
"""

import importlib
import logging
import os
import os.path
import shutil

import yaml

import pudl.constants as pc
import pudl.datastore.datastore as datastore

# from pudl import __file__ as pudl_pkg_file

logger = logging.getLogger(__name__)


def read_user_settings(settings_file=None):
    """Read the most basic PUDL settings from a user supplied file."""
    if settings_file is None:
        settings_file = os.path.join(os.path.expanduser('~'), '.pudl.yml')

    with open(settings_file, 'r') as f:
        pudl_settings = yaml.safe_load(f)

    return pudl_settings


def init(pudl_in=None, pudl_out=None, settings_file=None):
    """
    Generate commonly used PUDL settings based on a user settings file.

    If no configuration file path is provided, attempt to read in the user
    configuration from a file called .pudl.yml in the user's HOME directory.
    Presently the only values we expect are pudl_in and pudl_out, directories
    that store files that PUDL either depends on that rely on PUDL.

    Args:
        settings_file (path-like): A string or path like object that can be
            used to open a file containing the configuration. Defaults to
            $HOME/.pudl.yml

    Returns:
        dict: A dictionary containing common PUDL settings, derived from those
            read out of the YAML file.

    """
    # If we are missing either of the PUDL directories, try and read settings:
    if pudl_in is None or pudl_out is None:
        pudl_settings = read_user_settings(settings_file)
    else:
        pudl_settings = {}

    # If we have either of the inputs... use them to override what we read in:
    if pudl_in is not None:
        pudl_settings['pudl_in'] = pudl_in
    if pudl_out is not None:
        pudl_settings['pudl_out'] = pudl_out

    # Now construct the other settings:
    pudl_settings['data_dir'] = os.path.join(pudl_settings['pudl_in'], 'data')
    pudl_settings['settings_dir'] = \
        os.path.join(pudl_settings['pudl_in'], 'settings')
    pudl_settings['nb_dir'] = \
        os.path.join(pudl_settings['pudl_out'], 'notebooks')

    # We don't need to create the other data directories because they are more
    # complicated, and that task is best done by the datastore module.

    # These DB connection dictionaries are used by sqlalchemy.URL() (Using
    # 127.0.0.1, the numeric equivalent of localhost, to make postgres use the
    # `.pgpass` file without fussing around in the config.) sqlalchemy.URL will
    # make a URL missing post (therefore using the default), and missing a
    # password (which will make the system look for .pgpass)
    pudl_settings['db_pudl'] = {
        'drivername': 'postgresql',
        'host': '127.0.0.1',
        'username': 'catalyst',
        'database': 'pudl'
    }

    pudl_settings['db_pudl_test'] = {
        'drivername': 'postgresql',
        'host': '127.0.0.1',
        'username': 'catalyst',
        'database': 'pudl_test'
    }

    pudl_settings['ferc1_sqlite_url'] = "sqlite:///" + os.path.join(
        pudl_settings['pudl_out'], 'sqlite', 'ferc1.sqlite')

    pudl_settings['ferc1_test_sqlite_url'] = "sqlite:///" + os.path.join(
        pudl_settings['pudl_out'], 'sqlite', 'ferc1_test.sqlite')

    return pudl_settings


def setup(pudl_settings=None):
    """Set up a new PUDL working environment based on the user settings."""
    # If we aren't given settings, try and generate them.
    if pudl_settings is None:
        pudl_settings = init()

    # First directories for all of the data sources:
    os.makedirs(os.path.join(pudl_settings['data_dir'], 'tmp'), exist_ok=True)
    for source in pc.data_sources:
        src_dir = datastore.path(source, year=None, file=False,
                                 data_dir=pudl_settings['data_dir'])
        os.makedirs(src_dir, exist_ok=True)

    # Now the settings files:
    os.makedirs(pudl_settings['settings_dir'], exist_ok=True)
    settings_files = [
        'settings_init_pudl_default.yml',
        'settings_ferc1_to_sqlite_default.yml'
    ]
    for fn in settings_files:
        with importlib.resources.path('pudl.package_data.settings', fn) as f:
            dest_file = os.path.join(pudl_settings['settings_dir'], fn)
            if not os.path.exists(dest_file):
                shutil.copy(f, dest_file)

    # Now the output directories:
    for format in ['sqlite', 'parquet', 'datapackage']:
        format_dir = os.path.join(pudl_settings['pudl_out'], format)
        os.makedirs(format_dir, exist_ok=True)
        pudl_settings[f'{format}_dir'] = format_dir

    # Copy over the example notebooks:
    os.makedirs(pudl_settings['nb_dir'], exist_ok=True)
    for nb in ['pudl_intro.ipynb', 'pudl_output_to_csv.ipynb']:
        with importlib.resources.path('pudl.package_data.notebooks', nb) as f:
            dest_file = os.path.join(pudl_settings['nb_dir'], nb)
            if not os.path.exists(dest_file):
                shutil.copy(f, dest_file)