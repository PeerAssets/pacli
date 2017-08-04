import sys, pickle
from binascii import hexlify, unhexlify
import gnupg, getpass
from pypeerassets.kutil import Kutil

class GpgKeystore:
    """
    Implements reading and writing from gpg encrypted file.
    python-gnupg is a wrapper around the gpg cli, which makes it inherently fragile
    Uses pickle because private keys are binary
    """

    def __init__(self, Settings, keyfile):
        assert Settings.keystore == "gnupg"

        self._key = Settings.gnupgkey
        self._keyfile = keyfile

        self._init_settings = dict(
            homedir=Settings.gnupgdir,
            use_agent=bool(Settings.gnupgagent == "True"),
            keyring='pubring.gpg',
            secring='secring.gpg')
        self.gpg = gnupg.GPG(**self._init_settings)

    def read(self) -> dict:
        password = getpass.getpass("Input gpg key password:")
        contents = open(self._keyfile, 'rb').read()

        if not len(contents):
            return {}

        decrypted = self.gpg.decrypt(contents, passphrase=password)

        assert decrypted.ok, decrypted.status
        return pickle.loads(unhexlify(str(decrypted).encode()))

    def write(self, data: dict) -> str:
        encrypted = self.gpg.encrypt(hexlify(pickle.dumps(data)).decode(), self._key)
        assert encrypted.ok, encrypted.status
        keyfile = open(self._keyfile, "w")
        keyfile.write(str(encrypted))
        keyfile.close()


class KeyedProvider:

    """
    Wraps a provider, shadowing it's private key management and deferring other logic.
    Uses an in-memory store to handle
        importprivkey, getaddressesbyaccount, listaccounts, and dumpprivkeys
    """

    @classmethod
    def __init__(self, provider, keys: dict = {}):
        self.provider = provider
        self.privkeys = keys

    @classmethod
    def __getattr__(self, name):
        return getattr(self.provider, name)

    @classmethod
    def importprivkey(self, privkey: str, label: str) -> int:
        """import <privkey> with <label>"""
        mykey = Kutil(network=self.provider.network, wif=privkey)

        if label not in self.privkeys.keys():
            self.privkeys[label] = []

        if mykey.privkey not in [key['privkey'] for key in self.privkeys[label]]:
            self.privkeys[label].append({ "privkey": mykey.privkey,
                "address": mykey.address })

    @classmethod
    def getaddressesbyaccount(self, label: str) -> list:
        if label in self.privkeys.keys():
            return [key["address"] for key in self.privkeys[label]]

    @classmethod
    def listaccounts(self) -> dict:
        return {key:0 for key in self.privkeys.keys()}

    @classmethod
    def dumpprivkeys(self) -> dict:
        return self.privkeys


