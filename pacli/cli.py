import argparse

def cli():

    parser = argparse.ArgumentParser(description='Simple CLI PeerAssets client.')
    subparsers = parser.add_subparsers(title="Commands",
                                       dest="command",
                                       description='valid subcommands')

    deck = subparsers.add_parser('deck', help='Deck manipulation.')
    deck.add_argument("-list", choices=['all', 'subscribed'],
                      help="list decks")
    deck.add_argument("-info", action="store", help="show details of <asset_id>")
    deck.add_argument("-subscribe", action="store", help="subscribe to <deck id>")
    deck.add_argument("-search", action="store", help='''search for decks by name, id,
                       issue mode, issuer or number of decimals.''')
    #deck.add_argument("-new", action="store", help="spawn new deck")

    return parser.parse_args()
