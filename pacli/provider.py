from pypeerassets import RpcNode, Cryptoid, Explorer, pautils
from pacli.config import Settings


def set_up(provider):
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

    kwargs = dict(network=Settings.network)

    if Settings.provider.lower() == "rpcnode":
        Provider = RpcNode

    elif Settings.provider.lower() == "cryptoid":
        Provider = Cryptoid

    elif Settings.provider.lower() == "explorer":
        Provider = Explorer

    else:
        raise Exception('invalid provider.')

    provider = Provider(**kwargs)
    set_up(provider)

    return provider


provider = configured_provider(Settings)


def change(utxo):
    '''decide what will be change address
    * default - pay back to largest utxo
    * standard - behave as wallet does - pay to new address
    '''

    if Settings.change == "default":
        m = max([i["amount"] for i in utxo["utxos"]])
        return [i["address"] for i in utxo["utxos"] if i["amount"] == m][0]

    if Settings.change == "standard":
        return provider.getnewaddress()
