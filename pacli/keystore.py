import keyring
from os import urandom
from btcpy.structs.crypto import PrivateKey


def generate_key():
    '''generate new random key'''

    return PrivateKey(bytearray(urandom(32))).hexlify()


def init_keystore() -> None:
    '''save key to the keystore'''

    if not keyring.get_password('pacli', 'key'):
        keyring.set_password("pacli", 'key', generate_key())


def load_key() -> PrivateKey:
    '''load key from the keystore'''

    init_keystore()

    key = keyring.get_password('pacli', 'key')

    return PrivateKey.unhexlify(key)
