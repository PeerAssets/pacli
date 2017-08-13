from terminaltables import AsciiTable
from datetime import datetime
from binascii import hexlify
#from pypeerassets import find_card_transfers, find_all_valid_decks, DeckState, Deck, load_deck_p2th_into_local_node
import pypeerassets as pa
import json
from pacli.config import Settings


def default_account_utxo(provider, amount):
    '''set default address to be used with pacli'''

    if "PACLI" not in provider.listaccounts().keys():
        addr = provider.getaddressesbyaccount("PACLI")
        print("\n", "Please fund this address: {addr}".format(addr=addr))
        return

    for i in provider.getaddressesbyaccount("PACLI"):
        try:
            return provider.select_inputs(amount, i)
        except ValueError:
            pass

    print("\n", "Please fund one of the following addresses: {addrs}".format(
          addrs=provider.getaddressesbyaccount("PACLI")))
    return



def get_state(provider, deck):
    '''return balances of this deck'''

    cards = pa.find_card_transfers(provider, deck)
    if cards:
        return pa.DeckState(cards)
    else:
        raise ValueError("No cards on this deck.")


def tstamp_to_iso(tstamp):
    '''make iso timestamp from unix timestamp'''

    return datetime.fromtimestamp(tstamp).isoformat()


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


class DeckBalances:
    '''Show balances of address tied with this deck.'''

    @classmethod
    def __init__(cls, deck, balances):
        assert isinstance(deck, pa.Deck)
        cls.balances = dict(balances)
        cls.deck = deck

        ## Deck table header
        cls.deck_table = [
            ## add subscribed column
            ("address", "balance")
        ]

        cls.table = AsciiTable(cls.deck_table, title="Deck id: " + cls.deck.asset_id + " ")

    @classmethod
    def dtl(cls, addr, balance):
        '''deck-to-list deck to table-printable list'''

        l = []
        l.append(addr)
        l.append(exponent_to_amount(balance,
                 cls.deck.number_of_decimals))

        return l

    @classmethod
    def pack_for_printing(cls):

        assert len(cls.balances) > 0, {"error": "No balances found!"}

        for k in cls.balances:
            cls.deck_table.append(
                cls.dtl(k, cls.balances[k])
            )


class ListDecks:

    @classmethod
    def __init__(cls, decks):
        cls.decks = list(decks)

    ## Deck table header
    deck_table = [
        ## add subscribed column
        ("asset ID", "asset name", "issuer", "mode")
    ]

    table = AsciiTable(deck_table, title="Decks")

    @classmethod
    def dtl(cls, deck):
        '''deck-to-list deck to table-printable list'''

        l = []
        l.append(deck["asset_id"][:20])
        l.append(deck["name"])
        l.append(deck["issuer"])
        l.append(deck["issue_mode"])

        return l

    @classmethod
    def pack_decks_for_printing(cls):

        assert cls.decks, {"error": "No decks found!"}

        for i in cls.decks:
            cls.deck_table.append(
                cls.dtl(i.__dict__)
            )


def find_deck(provider, key: str) -> list:
    '''find deck by <key>'''

    decks = list(pa.find_all_valid_decks(provider, deck_version=Settings.deck_version, prod=Settings.production))
    for i in decks:
        i.short_id = i.asset_id[:20]

    return [d for d in decks if key in d.__dict__.values()]


def deck_list(provider):
    '''list command'''

    decks = pa.find_all_valid_decks(provider=provider, deck_version=Settings.deck_version,
                                    prod=Settings.production)
    d = ListDecks(decks)
    d.pack_decks_for_printing()
    print(d.table.table)


def deck_subscribe(provider, deck_id):
    '''subscribe command, load deck p2th into local node, pass <deck_id>'''

    try:
        deck = find_deck(provider, deck_id)[0]
    except IndexError:
        print({"error": "Deck not found!"})
        return
    pa.load_deck_p2th_into_local_node(provider, deck)


def deck_search(provider, key):
    '''search commands, query decks by <key>'''

    decks = find_deck(provider, key)
    d = ListDecks(provider, decks)
    d.pack_decks_for_printing()
    print(d.table.table)


def deck_info(provider, deck_id):
    '''info commands, show full deck details'''

    try:
        deck = find_deck(provider, deck_id)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    info = DeckInfo(deck)
    info.pack_decks_for_printing()
    print(info.table.table)


def deck_balances(provider, deck_id):
    '''show deck balances'''

    try:
        deck = find_deck(provider, deck_id)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    balances = get_state(provider, deck).balances
    b = DeckBalances(deck, balances)
    b.pack_for_printing()
    print(b.table.table)


def deck_checksum(provider, deck_id):
    '''info commands, show full deck details'''

    try:
        deck = find_deck(provider, deck_id)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    deck_state = get_state(provider, deck)
    if deck_state.checksum:
        print("\n", "Deck checksum is correct.")
    else:
        print("\n", "Deck checksum is incorrect.")


def new_deck(provider, deck, broadcast):
    '''
    Spawn a new PeerAssets deck.

    pacli deck --new '{"name": "test", "number_of_decimals": 1, "issue_mode": "ONCE"}'

    Will return deck span txid.
    '''

    deck = json.loads(deck)
    deck["network"] = Settings.network
    deck["production"] = Settings.production
    #utxo = provider.select_inputs(0.02)  # we need 0.02 PPC
    utxo = default_account_utxo(provider, 0.02)
    if utxo:
        change_address = change(utxo)
    else:
        return
    raw_deck = pa.deck_spawn(pa.Deck(**deck),
                             inputs=utxo,
                             change_address=change_address
                             )
    raw_deck_spawn = hexlify(raw_deck).decode()
    signed = provider.signrawtransaction(raw_deck_spawn)

    if broadcast:
        txid = provider.sendrawtransaction(signed["hex"])
        print("\n", txid, "\n")

        deck["asset_id"] = txid
        d = pa.Deck(**deck)
        pa.load_deck_p2th_into_local_node(provider, d) # subscribe to deck
    else:
        print("\nraw transaction:\n", signed["hex"], "\n")


