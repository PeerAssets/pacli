import os
import keyring
from btcpy.structs.crypto import PrivateKey

if os.name == 'nt':
    from keyring.backends import Windows
    keyring.set_keyring(Windows.WinVaultKeyring())


def generate_key() -> PrivateKey:
    '''generate new random key'''

    return os.urandom(32).hex()


def init_keystore() -> None:
    '''save key to the keystore'''

    if not keyring.get_password('pacli', 'key'):
        keyring.set_password("pacli", 'key', generate_key())


def load_key() -> PrivateKey:
    '''load key from the keystore'''

    init_keystore()

    key = keyring.get_password('pacli', 'key')

    return key
