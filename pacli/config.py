import configparser
import sys
from .default_conf import default_conf

def write_default_config(conf_file=None):
    print("writing default config")
    config = configparser.ConfigParser()
    config["settings"] = default_conf
    if not conf_file:
        config.write()
    else:
        with open(conf_file, 'w') as configfile:
            config.write(configfile)

optional = {
    "keystore": "none",
    "gnupgdir": "",
    "gnupgagent": "", 
    "gnupgkey": ""
    }

required = { "network", "production", "loglevel", "change"  }

def read_conf(conf_file):
    config = configparser.ConfigParser()
    config.read(conf_file)
    try:
        settings = dict(config["settings"])
        assert set(settings.keys()).issuperset(required)
        for k, v in optional.items():
            settings[k] = settings.get(k, v)

    except:
        print("config is outdated, saving current default config to",conf_file+".sample")
        write_default_config(conf_file+".sample")
        raise

    if settings["network"].startswith("t"):
        settings["testnet"] = True

    return settings
