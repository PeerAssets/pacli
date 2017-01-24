from terminaltables import AsciiTable
from cli import cli
import pypeerassets as pa

def set_up():
    '''setup'''

    # check if provider is working as expected
    assert provider.getinfo()["connections"] > 0, {"error": "Not connected to network."}
    # check if PAPROD P2TH is loaded in local node
    if not provider.listtransactions("PAPROD"):
        pa.pautils.load_p2th_privkeys_into_node(provider)

    # load config

class ListDecks:

    @classmethod
    def __init__(cls, decks):
        cls.decks = decks

    ## Deck table header
    deck_table = [
        ## add subscribed column
        ("asset ID", "asset name", "issuer", "mode", "subscribed")
    ]

    table = AsciiTable(deck_table, title="Decks")

    @staticmethod
    def dtl(deck, subscribed=False):
        '''deck-to-list deck to table-printable list'''

        l = []
        l.append(deck["asset_id"])
        l.append(deck["name"])
        l.append(deck["issuer"])
        l.append(deck["issue_mode"])
        if provider.getaddressesbyaccount(deck["name"]):
            l.append(True)
        else:
            l.append(False)
            if subscribed:
                l.remove(deck)

        return l

    @classmethod
    def pack_decks_for_printing(cls):

        assert len(cls.decks) > 0, {"error": "No decks found!"}

        for i in cls.decks:
            cls.deck_table.append(
                cls.dtl(i.__dict__)
            )


def deck_list(l):

    if l == "all":
        d = ListDecks(pa.find_all_valid_decks(provider))
        d.pack_decks_for_printing()
        print(d.table.table)

    if l == "subscribed":
        d = ListDecks(pa.find_all_valid_decks(provider))
        d.pack_decks_for_printing()
        print(d.table.table)

def deck_subscribe(deck_id):
    '''subscribe to deck, pass <deck_id>'''
    deck = pa.find_deck(provider, deck_id)[0]
    pa.load_deck_p2th_into_local_node(provider, deck)

def deck_search(key):
    '''search decks by key'''

    decks = pa.find_deck(provider, key)
    d = ListDecks(decks)
    d.pack_decks_for_printing()
    print(d.table.table)

if __name__ == "__main__":

    provider = pa.RpcNode(testnet=True)
    set_up()
    args = cli()

    if args.command == "deck":
        if args.list:
            deck_list(args.list)
        if args.subscribe:
            deck_subscribe(args.subscribe)
        if args.search:
            deck_search(args.search)

