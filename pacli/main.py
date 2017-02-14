from datetime import datetime
from terminaltables import AsciiTable
from binascii import hexlify
from cli import cli
import pypeerassets as pa
import json

class Settings:
    pass

def set_up():
    '''setup'''

    # load config // this should be loaded from the file some day
    Settings.change_addr = "mwkFUPUrh6LsXyMvBY2mz6btiJjuTxGgT8"
    Settings.network = "tppc"
    Settings.prod = True
    Settings.testnet = provider.is_testnet

    # check if provider is working as expected
    assert provider.getinfo()["connections"] > 0, {"error": "Not connected to network."}
    # check if PA P2TH is loaded in local node
    if Settings.prod:
        if not provider.listtransactions("PAPROD"):
            pa.pautils.load_p2th_privkeys_into_node(provider)
    if not Settings.prod:
        if not provider.listtransactions("PATEST"):
            pa.pautils.load_p2th_privkeys_into_node(provider, prod=False)

def tstamp_to_iso(tstamp):
    '''make iso timestamp from unix timestamp'''

    return datetime.fromtimestamp(tstamp).isoformat()

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

class ListCards:

    @classmethod
    def __init__(cls, cards):
        cls.cards = cards

        ## Deck table header
        cls.card_table = [
            ## add subscribed column
            ("txid", "sender", "receiver", "amount", "type", "confirms")
        ]

        cls.table = AsciiTable(cls.card_table, title="Card transfers of deck:")

    @staticmethod
    def dtl(card, subscribed=False):
        '''cards-to-list cards to table-printable list'''

        l = []
        l.append(card["txid"])
        l.append(card["sender"])
        l.append(card["receivers"])
        l.append(card["amount"])
        l.append(card["type"])
        if card["blockhash"] != "Unconfirmed.":
            l.append(provider.gettransaction(card["txid"])["confirmations"])
        else:
            l.append(0)

        return l

    @classmethod
    def pack_cards_for_printing(cls):

        assert len(cls.cards) > 0, {"error": "No cards found!"}

        for i in cls.cards:
            cls.card_table.append(
                cls.dtl(i.__dict__)
            )


class DeckInfo:

    @classmethod
    def __init__(cls, deck):
        assert isinstance(deck, pa.Deck)
        cls.deck = deck

        ## Deck table header
        cls.deck_table = [
            ## add subscribed column
            ("asset name", "issuer", "issue mode", "decimals", "issue time")
        ]

        cls.table = AsciiTable(cls.deck_table, title="Deck id: " + cls.deck.asset_id + " ")

    @staticmethod
    def dtl(deck, subscribed=False):
        '''deck-to-list deck to table-printable list'''

        l = []
        l.append(deck["name"])
        l.append(deck["issuer"])
        l.append(deck["issue_mode"])
        l.append(deck["number_of_decimals"])
        l.append(tstamp_to_iso(deck["issue_time"]))

        return l

    @classmethod
    def pack_decks_for_printing(cls):

        cls.deck_table.append(cls.dtl(cls.deck.__dict__))

def deck_list(l):
    '''list command'''

    if l == "all":
        d = ListDecks(pa.find_all_valid_decks(provider))
        d.pack_decks_for_printing()
        print(d.table.table)

    if l == "subscribed":
        d = ListDecks(pa.find_all_valid_decks(provider))
        d.pack_decks_for_printing()
        print(d.table.table)

def deck_subscribe(deck_id):
    '''subscribe command, load deck p2th into local node, pass <deck_id>'''

    deck = pa.find_deck(provider, deck_id)[0]
    pa.load_deck_p2th_into_local_node(provider, deck)

def deck_search(key):
    '''search commands, query decks by <key>'''

    decks = pa.find_deck(provider, key)
    d = ListDecks(decks)
    d.pack_decks_for_printing()
    print(d.table.table)

def deck_info(deck_id):
    '''info commands, show full deck details'''

    deck = pa.find_deck(provider, deck_id)[0]
    info = DeckInfo(deck)
    info.pack_decks_for_printing()
    print(info.table.table)

def new_deck(deck):
    '''
    Spawn a new PeerAssets deck.

    pacli deck -new '{"name": "test", "number_of_decimals": 1, "issue_mode": "ONCE"}'

    Will return deck span txid.
    '''

    deck = json.loads(deck)
    utxo = provider.select_inputs(0.02) ## we need 0.02 PPC
    raw_deck = pa.deck_spawn(pa.Deck(**deck),
                             Settings.network,
                             utxo,
                             Settings.change_addr,
                             Settings.prod
                            )
    raw_deck_spawn = hexlify(raw_deck).decode()
    signed = provider.signrawtransaction(raw_deck_spawn)
    print("\n", provider.sendrawtransaction(signed["hex"]), "\n")

    pa.load_deck_p2th_into_local_node(provider, deck) # subscribe to deck

def list_cards(args):
    '''
    List cards of this <deck>.abs

    pacli card -list <deck>
    '''

    deck = pa.find_deck(provider, args)[0]
    if not provider.getaddressesbyaccount(deck.name):
        return({"error": "You must subscribe to deck to be able to list transactions."})

    c = ListCards(pa.find_all_card_transfers(provider, deck))
    c.pack_cards_for_printing()
    print(c.table.table)

def card_issue(args):
    '''
    Issue new cards of this deck.

    pacli card -issue '{"deck": "deck_id",
                        "receivers": [list of receiver addresses], "amounts": [list of amounts]
                        }
    '''

    issue = json.loads(args)
    deck = pa.find_deck(provider, issue["deck"])[0]
    if not provider.getaddressesbyaccount(deck.name):
        return {"error": "You are not even subscribed to this deck, how can you issue cards?"}
    try:
        utxo = provider.select_inputs(0.02, deck.issuer):
    except ValueError:
        return {"error": "You are not owner of this deck, you can not issue cards."}

    ct = pa.CardTransfer(deck, issue["receivers"], issue["amounts"])
    raw_ct = hexlify(pa.card_issue(deck, ct, utxo,
                                   utxo["utxos"][0]["address"],
                                   Settings.testnet,
                                   Settings.prod)
                    ).decode()

    signed = provider.signrawtransaction(raw_ct)
    print("\n", provider.sendrawtransaction(signed["hex"]), "\n") # send the tx

def card_burn(args):
    '''
    Burn cards of this deck.

    pacli card -burn '{"deck": "deck_id", "amount": ["amount"]}'
    '''

    args = json.loads(args)
    deck = pa.find_deck(provider, args["deck"])[0]
    if not provider.getaddressesbyaccount(deck.name):
        return({"error": "You are not even subscribed to this deck, how can you burn cards?"})

    utxo = provider.select_inputs(0.02)
    cb = pa.CardTransfer(deck, [deck.issuer], args["amounts"])
    raw_cb = hexlify(pa.card_burn(deck, cb, utxo,
                                   Settings.change_addr,
                                   Settings.testnet,
                                   Settings.prod)
                    ).decode()

    signed = provider.signrawtransaction(raw_cb)
    print("\n", provider.sendrawtransaction(signed["hex"]), "\n") # send the tx

def card_transfer(args):
    '''
    Transfer cards to <receivers>

    pacli card -transfer '{"deck": "deck_id",
                        "receivers": [list of receiver addresses], "amounts": [list of amounts]
                        }
    '''

    args = json.loads(args)
    deck = pa.find_deck(provider, args["deck"])[0]
    if not provider.getaddressesbyaccount(deck.name):
        return({"error": "You are not even subscribed to this deck, how can you transfer cards?"})

    utxo = provider.select_inputs(0.02)
    ct = pa.CardTransfer(deck, args["receivers"], args["amounts"])
    raw_ct = hexlify(pa.card_transfer(deck, ct, utxo,
                                      Settings.change_addr,
                                      Settings.testnet,
                                      Settings.prod)
                    ).decode()

    signed = provider.signrawtransaction(raw_ct)
    print("\n", provider.sendrawtransaction(signed["hex"]), "\n") # send the tx


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
        if args.info:
            deck_info(args.info)
        if args.new:
            new_deck(args.new)

    if args.command == "card":
        if args.issue:
            card_issue(args.issue)
        if args.burn:
            card_burn(args.burn)
        if args.transfer:
            card_transfer(args.transfer)
        if args.list:
            list_cards(args.list)

