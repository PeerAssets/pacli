from pypeerassets import RpcNode, Holy, Cryptoid
from pacli.keystore import GpgKeystore, as_local_key_provider

def set_up(provider):
    '''setup'''

    # if provider is local node, check if PA P2TH is loaded in local node
    # this handles indexing of transaction
    if Settings.provider == "rpcnode":
        if Settings.production:
            if not provider.listtransactions("PAPROD"):
                pa.pautils.load_p2th_privkeys_into_local_node(provider)
        if not Settings.production:
            if not provider.listtransactions("PATEST"):
                pa.pautils.load_p2th_privkeys_into_local_node(provider, prod=False)
   #elif Settings.provider != 'holy':
   #    pa.pautils.load_p2th_privkeys_into_local_node(provider, keyfile)

def configured_provider(Settings):
    " resolve settings into configured provider "

    if Settings.provider.lower() == "rpcnode":
        Provider = RpcNode
        kwargs = dict(testnet=Settings.testnet)

    elif Settings.provider.lower() == "holy":
        Provider = Holy
        kwargs = dict(network=Settings.network)

    elif Settings.provider.lower() == "cryptoid":
        Provider = Cryptoid
        kwargs = dict(network=Settings.network)

    else:
        raise Exception('invalid provider')

    if Settings.keystore.lower() == "gnupg":
        Provider = as_local_key_provider(Provider)
        kwargs['keystore'] = keystore = GpgKeystore(Settings)

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


