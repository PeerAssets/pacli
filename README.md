# pacli

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI](https://img.shields.io/pypi/v/pacli.svg?style=flat-square)](https://pypi.python.org/pypi/pacli/)
[![](https://img.shields.io/badge/python-3.5+-blue.svg)](https://www.python.org/download/releases/3.5.0/) 


This simple PeerAssets client is implemented using the [pypeerassets](https://github.com/PeerAssets/pypeerassets) Python library.
This command line program is useful as companion utility during PeerAssets development and testing. It is built for console usage via intuitive and easy to learn set of commands.
It stores the privkey in OS's native keystore, which is automatically unlocked upon logging into active user session.
It handles only one key for now, until HD key support is implemented.

Main config file is located in `$HOME/.config/pacli`.

## installation

### linux

*pacli is meant for desktop environment (Gnome/KDE), if you want to run it headless see this: https://github.com/jaraco/keyring#using-keyring-on-headless-linux-systems*

`python3 setup.py install --user`

To access it from the command line, place the following in $HOME/.bashrc:

`export PATH=$PATH:$HOME/.local/bin`

`source ~/.bashrc`

__________________________________________________

## examples:

> pacli -- --help

show all commands

> pacli address show [--privkey, --pubkey, --wif]

show current address, or it's privkey, pubkey or wif

> pacli address balance

show balance of the current address

[![asciicast](https://asciinema.org/a/J1NLGEgdRcSE7ppLp48Lu2bD7.png)](https://asciinema.org/a/J1NLGEgdRcSE7ppLp48Lu2bD7)

> pacli address derive STRING

derive a new address from STRING, useful for P2TH experimentations

> pacli deck search $KEY

search for deck by key, can be deck_id, name, issuer, issue_mode or else

> pacli deck info $DECK_ID

show full deck details

> pacli deck list all

list all decks on the network

[![asciicast](https://asciinema.org/a/tIHxrZIGIvEalC1PzkyenikUh.png)](https://asciinema.org/a/tIHxrZIGIvEalC1PzkyenikUh)

> pacli deck my

show decks issued by the address I control

> pacli deck spawn --name "My own asset" --number_of_decimals 1 issue_mode 4

issue a new asset named "My own asset", it will return a hexlified raw transaction.

[![asciicast](https://asciinema.org/a/l4MAPXBbXc5ufn5UdS2r0QEHj.png)](https://asciinema.org/a/l4MAPXBbXc5ufn5UdS2r0QEHj)

> pacli deck decode $HEX

decode protobuf message and display it as json, usable when debbuging decks

> pacli deck encode --name "My own asset" --number_of_decimals 1 issue_mode 4

encode the deck information into hex to be inserted in OP_RETURN, usable when creating decks using something like cointoolkit

> pacli deck spawn --name "My own asset" --number_of_decimals 1 issue_mode 4 --verify

--verify flag presents a link to external tool `cointoolkit` which can be used to preview or debug the deck spawn transaction.

> pacli deck issue_mode --list

list all supported issue modes and their values

> pacli card list *deck_id*

list all card transfers related to this deck

> pacli card balance *deck_id*

show balances of addresses on this deck

> pacli deck --checksum *deck_id*

verify deck checksum, checksum is difference between issued cards and balances of all the addresses.
If it is not zero, something is wrong with deck balances. This function will return True if all is fine.

> pacli card new --deckid $DECKID --receiver [address, address2] --amount [200]

fabricate a new CardTransfer object.

> pacli card transfer --deckid 078f41c257642a89ade91e52fd484c141b11eda068435c0e34569a5dfcce7915 --receiver [n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj] --amount [200] --verify

farbricate a new CardTransfer, and link to external tool `cointoolkit` to verify the transaction.

> pacli card encode --deckid 078f41c257642a89ade91e52fd484c141b11eda068435c0e34569a5dfcce7915 --receiver [n12h8P5LrVXozfhEQEqg8SFUmVKtphBetj] --amount [200]

encode the deck information into hex to be inserted in OP_RETURN, usable when creating decks using something like cointoolkit

> pacli card decode $HEX

decode protobuf message and display it as json, usable when debbuging cards

> pacli card burn --deckid 078f41c257642a89ade91e52fd484c141b11eda068435c0e34569a5dfcce7915 --receiver [$DECK_ISSUE_ADDRESS] --amount [11] --verify

burn 11 of card on this deck.

> pacli card issue --deckid 078f41c257642a89ade91e52fd484c141b11eda068435c0e34569a5dfcce7915 --receiver [n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x] --amount [110] --verify

issue 110 cards to n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x.

> pacli card export *filename*

export the card transactions to .csv file

## bash completion (on *nix platforms)

Create file `.bash_completion` with content:

```
for bcfile in ~/.bash_completion.d/* ; do
    . $bcfile
done
```

Create directory: `mkdir ~/.bash_completion.d`

Export completion file:

`pacli -- --completion >> .bash_completion.d/pacli`

Activate:

`. ~/.bash_completion`

Tab away.
