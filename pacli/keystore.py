import gnupg
import getpass
import sys
from pypeerassets.kutil import Kutil

mypg = None

def read_keystore(Settings,keyfile) -> str:
    mykeys = ""

    if Settings.keystore == "gnupg" and Settings.provider != "rpcnode":
        mypg = gnupg.GPG(binary='/usr/bin/gpg',homedir=Settings.gnupgdir,use_agent=bool(Settings.gnupgagent=="True"),keyring='pubring.gpg',secring='secring.gpg')
        password = getpass.getpass("Input gpg key password:")
        fd = open(keyfile)
        data = fd.read()

        if len(data)>0:
            mykeys = str(mypg.decrypt(data,passphrase=password))
        fd.close()
    else:
        print("using rpcnode")

    return mykeys

def write_keystore(Settings,keyfile,keys):

    if mypg:
        data = str(mypg.encrypt(str(keys),Settings.gnupgkey))
        fd = open(keyfile,"w")
        fd.write(data)
        fd.close()

class KeyedProvider:

    """
    Keystore class
    """

    @classmethod
    def __init__(self, provider, keysJson: str=""):
        """
        : 
        """
        self.provider = provider

        if keysJson != "":
            self.privkeys = eval(keysJson)
        else:
            self.privkeys = {}

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
            self.privkeys[label].append({
                "privkey": mykey.privkey,
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
