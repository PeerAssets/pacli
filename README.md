# pacli

> Licence: GPL3

> Language: Python (>= 3.5)

Simple CLI PeerAssets client.

Implemented using `pypeerassets` Python library, this command line program is useful as companion utility during PeerAssets development and testing.
It is built for headless (CLI) usage via intuitive and easy to learn set of commands.

It stores the privkey in OS's native keystore, which is automatically unlocked upon logging into active user session.
It handles only one key for now, until HD key support is not implemented.

Main config file is located in `$HOME/.config/pacli`.

## installation

### linux

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

> pacli deck search "My little pony"

search for deck called "My little pony"

> pacli deck info $DECK_ID

show full deck details

> pacli deck list all

list all decks on the network

> pacli deck spawn --name "My own asset" --number_of_decimals 1 issue_mode 4

issue a new asset named "My own asset", it will return a hexlified raw transaction.

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

> pacli card burn --deckid 078f41c257642a89ade91e52fd484c141b11eda068435c0e34569a5dfcce7915 --receiver [n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x] --amount [110] --verify

issue 110 cards to n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x.
