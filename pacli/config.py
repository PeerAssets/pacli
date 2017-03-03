import configparser
from .default_conf import default_conf

def write_default_config(conf_file):
    print("writing default config")
    config = configparser.ConfigParser()
    config["settings"] = default_conf
    with open(conf_file, 'w') as configfile:
        config.write(configfile)

def read_conf(conf_file):
    config = configparser.ConfigParser()
    config.read(conf_file)
    settings = {
        "network": config["settings"]["network"],
        "production": config["settings"]["production"],
        "loglevel": config["settings"]["loglevel"],
        "change": config["settings"]["change"]
        }

    if settings["network"].startswith("t"):
        settings["testnet"] = True

    return settings
