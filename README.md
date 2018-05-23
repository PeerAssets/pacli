# pacli

> Licence: GPL3

> Language: Python (>= 3.5)

Simple CLI PeerAssets client.

Implemented using `pypeerassets` Python library, this command line program is useful as companion utility during PeerAssets development and testing.
It is built for headless (CLI) usage via intuitive and easy to learn set of commands.

It stores the privkey in OS's native keystore, which is automatically unlocked upon logging into active user session.
It handles only one key for now, until HD key support is not implemented.

Main config file is located in `$HOME/.config/pacli`.

Examples:

> pacli -- --help

show all commands

> pacli address show [--privkey, --pubkey, --wif]

show current address, or it's privkey, pubkey or wif

> pacli address balance

show balance of the current address

> pacli deck search "My little pony"

search for deck called "My little pony"

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

> pacli card burn '{"deck": "d460651e1d9147770ec9d4c254bcc68ff5d203a86b97c09d00955fb3f714cab3", "amounts": [11]}'

burn 11 of card on this deck, this transaction will be denied if you have no cards on this deck.

> pacli card issue '{"deck": "hopium_v2", "receiver": ["n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x"], "amount": [110]}'

issue 110 cards to n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x, this transaction will be declined if you do not own deck issuing address.

> pacli card transfer '{"deck": "08c1928ce84d9066f120", "receiver": ["n1GqTk2NFvSCX3h78rkEA3DoiJW8QxT3Mm", "mv8J47BV8ahpKq7dNXut3kXPgQQCQea5FR",
                         "myeFFDLXvpGUh8gBPZdCNEsLQ7ZPZkH7d8"], "amount": [1, 9.98, 200.1]}'

transfer cards of "08c1928ce84d9066f120" deck (queried by short id, it is clementines deck) to three different addresses.
This transaction will be denied if you have no address which holds cards of this deck or if your balance is not sufficient.

> pacli vote new '{"deck": "hopium_v2", "choices": ["y", "n"], "count_mode": "SIMPLE", "description": "yes or no?", "start_block": 27306, "end_block": 27310}'

create new vote on the "hopium_v2" deck with choices "y" and "no", starting from block 27306 and lasting until block 27310.

> pacli vote list "hopium_v2"

Shows all the votes on this deck.

```
+Votes on this deck:-----------------------------------------------+------------------------------------+------------------+-------------+-----------+
| vote_id                                                          | sender                             | description      | start_block | end_block |
+------------------------------------------------------------------+------------------------------------+------------------+-------------+-----------+
| 7459c9f4738001e3c50653d6066e3d41a9ffb2a1f3d786721bc472bcb04f17fa | msYThv5bf7KjhHT1Cj5D7Y1tofyhq9vhWM | PPC to the moon? | 268400      | 290000    |
| 79e940296f26feb3e5ebaaea0d9aced153e796926e8db926050977ae02c00fa6 | msYThv5bf7KjhHT1Cj5D7Y1tofyhq9vhWM | test1            | 27306       | 275000    |
+------------------------------------------------------------------+------------------------------------+------------------+-------------+-----------+
```

> pacli vote cast '{"vote": "7459c9f4738001e3c50653d6066e3d41a9ffb2a1f3d786721bc472bcb04f17fa", choice: "yes"}'

cast "yes" vote to vote_id 7459c9f4738001e3c50653d6066e3d41a9ffb2a1f3d786721bc472bcb04f17fa

_____________________________________

This is a early release based on unfinished pypeerassets library.
