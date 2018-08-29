from pypeerassets.transactions import (MutableTransaction,
                                       sign_transaction
                                       )

from pacli.provider import provider
from pacli.config import Settings


def cointoolkit_verify(hex: str) -> str:
    '''tailor cointoolkit verify URL'''

    base_url = 'https://indiciumfund.github.io/cointoolkit/'
    if provider.network == "peercoin-testnet":
        mode = "mode=peercoin_testnet"
    if provider.network == "peercoin":
        mode = "mode=peercoin"

    return base_url + "?" + mode + "&" + "verify=" + hex


def signtx(rawtx: MutableTransaction) -> str:
    '''sign the transaction'''

    return sign_transaction(provider, rawtx, Settings.key)


def sendtx(signed_tx: MutableTransaction) -> str:
    '''send raw transaction'''

    provider.sendrawtransaction(signed_tx.hexlify())

    return signed_tx.txid
