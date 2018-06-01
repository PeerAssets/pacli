from pypeerassets import RpcNode, Cryptoid, Explorer, pautils
from pacli.config import Settings


def set_up():
    '''setup'''

    # if provider is local node, check if PA P2TH is loaded in local node
    # this handles indexing of transaction
    if Settings.provider == "rpcnode":
        if Settings.production:
            if not provider.listtransactions("PAPROD"):
                pautils.load_p2th_privkeys_into_local_node(provider)
        if not Settings.production:
            if not provider.listtransactions("PATEST"):
                pautils.load_p2th_privkeys_into_local_node(provider, prod=False)


def configured_provider(Settings):
    " resolve settings into configured provider "

    if Settings.provider.lower() == "rpcnode":
        _provider = RpcNode

    elif Settings.provider.lower() == "cryptoid":
        _provider = Cryptoid

    elif Settings.provider.lower() == "explorer":
        _provider = Explorer

    else:
        raise Exception('invalid provider.')

    provider = _provider(network=Settings.network)
    set_up()

    return provider


provider = configured_provider(Settings)
