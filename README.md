# pacli
Simple CLI PeerAssets client. 

Implemented using `pypeerassets` Python library, this command line program is useful as companion utility during PeerAssets development and testing.
It is built for headless (CLI) usage via intuitive and easy to learn set of commands.
All deck id's are shortened by taking only 20 first characters of full sha256 deck id, this is to allow easier user interaction
and use less screen space. You can always get full deck id by calling `pacli -info` command as shown bellow.
When querying for deck you can use short deck id, full deck id and deck name.
Using short or full deck id is advised as decks can have a same name.


Examples:

> pacli -h

show all commands

> pacli -status

show current network, all subscribed decks and their card balances

> pacli deck -search "My little pony"

search for deck called "My little pony"

> pacli deck -list all

list all decks on the network

> pacli deck -info *deck_id*

show detail deck information,
use this command if you need full deck ID hash and not shortened id.

> pacli deck -subscribe *deck_id*

subscribe to this deck to enable balances and card listing for this deck

> pacli deck -balance *deck_id*

show balances of all addresses involved with this deck

Complex operations take JSON-like sturucture as argument, mimicking peercoind JSON-RPC interface.
* amount variable is always a list
* receiver variable is always a list

> pacli deck -new '{"name": "My own asset", "number_of_decimals": 1, "issue_mode": "ONCE"}'

issue a new asset named "My own asset".

> pacli card -list *deck_id*

list all card transfers related to this deck

> pacli deck -checksum *deck_id*

verify deck checksum, checksum is difference between issued cards and balances of all the addresses.
If it is not zero, something is wrong with deck balances. This function will return True if all is fine.

> pacli card -burn '{"deck": "d460651e1d9147770ec9d4c254bcc68ff5d203a86b97c09d00955fb3f714cab3", "amounts": [11]}'

burn 11 of card on this deck, this transaction will be denied if you have no cards on this deck.

> pacli card -issue '{"deck": "hopium_v2", "receiver": ["n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x"], "amount": [110]}'

issue 110 cards to n29g3XjvxqWLKgEkyg4Z1BmgrJLccqiH3x, this transaction will be declined if you do not own deck issuing address.

> pacli card -transfer '{"deck": "08c1928ce84d9066f120", "receiver": ["n1GqTk2NFvSCX3h78rkEA3DoiJW8QxT3Mm", "mv8J47BV8ahpKq7dNXut3kXPgQQCQea5FR",
                         "myeFFDLXvpGUh8gBPZdCNEsLQ7ZPZkH7d8"], "amount": [1, 9.98, 200.1]}'

transfer cards of "08c1928ce84d9066f120" deck (queried by short id, it is clementines deck) to three different addresses.
This transaction will be denied if you have no address which holds cards of this deck or if your balance is not sufficient.

_____________________________________

This is a early release based on unfinished pypeerassets library.
