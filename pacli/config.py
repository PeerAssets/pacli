from typing import Union
from appdirs import user_config_dir
import configparser
import os
from pacli.keystore import load_key
from pypeerassets.pa_constants import param_query
from pacli.default_conf import default_conf
from pypeerassets import Kutil


conf_dir = user_config_dir("pacli")
conf_file = os.path.join(conf_dir, "pacli.conf")
logfile = os.path.join(conf_dir, "pacli.log")


def write_default_config(conf_file=None):
    '''if config file is not found, write a new one'''

    print("writing default config")
    config = configparser.ConfigParser()
    config["settings"] = default_conf
    if not conf_file:
        config.write()
    else:
        with open(conf_file, 'w') as configfile:
            config.write(configfile)


required = {"network", "deck_version", "production", "change", "provider"}


def read_conf(conf_file):

    config = configparser.ConfigParser()
    config.read(conf_file)

    settings = dict(config["settings"])
    if not set(settings.keys()).issuperset(required):

        print("config is outdated, saving current default config to", conf_file)
        write_default_config(conf_file + ".sample")

    if settings["network"].startswith("t"):
        settings["testnet"] = True

    settings['p2th_address'] = param_query(settings['network']).P2TH_addr

    return settings


def init_config():
    '''if first run, setup local configuration directory.'''

    if not os.path.isdir(conf_dir):
        os.makedirs(conf_dir)
    if not os.path.exists(conf_file):
        write_default_config(conf_file)


def load_conf():
    '''load user configuration'''

    init_config()

    class Settings:
        pass

    settings = read_conf(conf_file)

    for key in settings:
        setattr(Settings, key, settings[key])

    setattr(Settings, 'deck_version', int(Settings.deck_version))
    setattr(Settings, 'key', Kutil(network=settings['network'],
                                   privkey=bytearray.fromhex(load_key())
                                   )
            )

    if settings['change'] == "default":
        Settings.change = Settings.key.address

    return Settings


def write_settings(key: str, value: Union[str, bool]) -> None:
    '''write new conf file'''

    config = configparser.ConfigParser()
    config.read(conf_file)

    config['settings'][key] = value

    with open(conf_file, 'w') as configfile:
        config.write(configfile)


Settings = load_conf()
