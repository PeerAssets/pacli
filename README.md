# pacli
Simple CLI PeerAssets client. 

Implemented using `pypeerassets` Python library, this program is useful as companion utility during PeerAssets development.
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


This is early release based on unfinished pypeerassets library.