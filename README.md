# pacli
Simple CLI PeerAssets client. 

Implemented using `pypeerassets` Python library, this command line program is useful as companion utility during PeerAssets development and testing.
It is built for headless (CLI) usage via intuitive and easy to learn set of commands.

Examples:

> pacli -h

show all commands

> pacli deck -search "My little pony"

search for deck called "My little pony"

> pacli deck -list all

list all decks on the network

> pacli deck -subscribe *deck_id*

subscribe to this deck to enable building a proof-of-timeline for the deck

> pacli deck -new '{"name": "My own asset", "number_of_decimals": 1, "issue_mode": "ONCE"}'

issue a new asset named "My own asset".

> pacli card -list <deck_id_hash>

list all card transfers related to this deck

> pacli card -burn '{"deck": "d460651e1d9147770ec9d4c254bcc68ff5d203a86b97c09d00955fb3f714cab3", "amounts": [11]}'

burn 11 of card on this deck

_____________________________________

This is a early release based on unfinished pypeerassets library.