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

def read_conf(conf_file):
    config = configparser.ConfigParser()
    config.read(conf_file)
    try:
        settings = {
            "network": config["settings"]["network"],
            "production": config["settings"]["production"],
            "loglevel": config["settings"]["loglevel"],
            "change": config["settings"]["change"],
            "provider": config["settings"]["provider"],
            "keystore": config["settings"]["keystore"],
            "gnupgdir": config["settings"]["gnupgdir"],
            "gnupgagent": config["settings"]["gnupgagent"],
            "gnupgkey": config["settings"]["gnupgkey"]
            }
    except:
        print("config is outdated, saving current default config to",conf_file+".sample")
        write_default_config(conf_file+".sample")
        raise

    if settings["network"].startswith("t"):
        settings["testnet"] = True

    return settings
