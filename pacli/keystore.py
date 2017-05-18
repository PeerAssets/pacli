import gnupg
import getpass
import sys

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
    
