from datetime import datetime
from terminaltables import AsciiTable
from binascii import hexlify
from appdirs import user_config_dir
from pacli.config import write_default_config, read_conf
import os, argparse
import pypeerassets as pa
from pypeerassets.pautils import amount_to_exponent, exponent_to_amount
import json
import logging

conf_dir = user_config_dir("pacli")
conf_file = os.path.join(conf_dir, "pacli.conf")
logfile = os.path.join(conf_dir, "pacli.log")

class Settings:
    pass

def load_conf():
    '''load user configuration'''

    user_config = read_conf(conf_file)
    for key in user_config:
        setattr(Settings, key, user_config[key])

    logging.basicConfig(filename=logfile, level=logging.getLevelName(Settings.loglevel))
    logging.basicConfig(level=logging.getLevelName(Settings.loglevel),
                        format="%(asctime)s %(levelname)s %(message)s")

    logging.debug("logging initialized")

def first_run():
    '''if first run, setup local configuration directory.'''

    if not os.path.exists(conf_dir):
        os.mkdir(conf_dir)
    if not os.path.exists(conf_file):
        write_default_config(conf_file)

def set_up(provider):
    '''setup'''

    # check if provider is working as expected
    assert provider.getinfo()["connections"] > 0, {"error": "Not connected to network."}
    # check if PA P2TH is loaded in local node
    if Settings.production:
        if not provider.listtransactions("PAPROD"):
            pa.pautils.load_p2th_privkeys_into_local_node(provider)
    if not Settings.production:
        if not provider.listtransactions("PATEST"):
            pa.pautils.load_p2th_privkeys_into_local_node(provider, prod=False)

def change(utxo):
    '''decide what will be change address
    * default - pay back to largest utxo
    * standard - behave as wallet does - pay to new address
    '''

    if Settings.change == "default":
        m = max([i["amount"] for i in utxo["utxos"]])
        return [i["address"] for i in utxo["utxos"] if i["amount"] == m][0]

    if Settings.change == "standard":
        return provider.getnewaddress()

def tstamp_to_iso(tstamp):
    '''make iso timestamp from unix timestamp'''

    return datetime.fromtimestamp(tstamp).isoformat()


def find_deck(provider, key: str) -> list:
    '''find deck by <key>'''

    decks = pa.find_all_valid_decks(provider, prod=Settings.production)
    for i in decks:
        i.short_id = i.asset_id[:20]

    return [d for d in decks if key in d.__dict__.values()]


class ListDecks:

    @classmethod
    def __init__(cls, provider, decks):
        cls.provider = provider
        cls.decks = decks

    ## Deck table header
    deck_table = [
        ## add subscribed column
        ("asset ID", "asset name", "issuer", "mode", "subscribed")
    ]

    table = AsciiTable(deck_table, title="Decks")

    @classmethod
    def dtl(cls, deck, subscribed=False):
        '''deck-to-list deck to table-printable list'''

        l = []
        l.append(deck["asset_id"][:20])
        l.append(deck["name"])
        l.append(deck["issuer"])
        l.append(deck["issue_mode"])
        if cls.provider.getaddressesbyaccount(deck["name"]):
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
    def __init__(cls, provider, cards):
        cls.provider = provider
        cls.cards = cards

        ## Deck table header
        cls.card_table = [
            ## add subscribed column
            ("txid", "sender", "receiver", "amount", "type", "confirms")
        ]

        cls.table = AsciiTable(cls.card_table, title="Card transfers of this deck:")

    @classmethod
    def dtl(cls, card, subscribed=False):
        '''cards-to-list cards to table-printable list'''

        l = []
        l.append(card["txid"][:20])
        l.append(card["sender"])
        l.append(card["receiver"][0])
        l.append(exponent_to_amount(card["amount"][0],
                 card["number_of_decimals"]))
        l.append(card["type"])
        if card["blockhash"] != 0:
            l.append(cls.provider.gettransaction(card["txid"])["confirmations"])
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

def deck_list(provider, l):
    '''list command'''

    if l == "all":
        d = ListDecks(provider, pa.find_all_valid_decks(provider))
        d.pack_decks_for_printing()
        print(d.table.table)

    if l == "subscribed":
        d = ListDecks(provider, pa.find_all_valid_decks(provider))
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

def new_deck(provider, deck):
    '''
    Spawn a new PeerAssets deck.

    pacli deck -new '{"name": "test", "number_of_decimals": 1, "issue_mode": "ONCE"}'

    Will return deck span txid.
    '''

    deck = json.loads(deck)
    deck["network"] = Settings.network
    deck["production"] = Settings.production
    utxo = provider.select_inputs(0.02) ## we need 0.02 PPC
    change_address = change(utxo)
    raw_deck = pa.deck_spawn(pa.Deck(**deck),
                             inputs=utxo,
                             change_address=change_address
                            )
    raw_deck_spawn = hexlify(raw_deck).decode()
    signed = provider.signrawtransaction(raw_deck_spawn)
    txid = provider.sendrawtransaction(signed["hex"])
    print("\n", txid, "\n")

    deck["asset_id"] = txid
    d = pa.Deck(**deck)
    pa.load_deck_p2th_into_local_node(provider, d) # subscribe to deck

def list_cards(provider, args):
    '''
    List cards of this <deck>.abs

    pacli card -list <deck>
    '''

    try:
        deck = find_deck(provider, args)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    if not provider.getaddressesbyaccount(deck.name):
        print("\n", {"error": "You must subscribe to deck to be able to list transactions."})
        return

    c = ListCards(provider, pa.find_card_transfers(provider, deck))
    c.pack_cards_for_printing()
    print(c.table.table)

def card_issue(provider, args):
    '''
    Issue new cards of this deck.

    pacli card -issue '{"deck": "deck_id",
                        "receivers": [list of receiver addresses], "amounts": [list of amounts]
                        }
    '''

    issue = json.loads(args)
    try:
        deck = find_deck(provider, issue["deck"])[0]
    except IndexError:
        print("\n", {"error": "Deck not found."})
        return
    if provider.validateaddress(deck.issuer)["ismine"]:
            try:
                utxo = provider.select_inputs(0.02, deck.issuer)
            except ValueError:
                print("\n", {"error": "Please send funds to the issuing address."})
                return
    else:
        print("\n", {"error": "You are not the owner of this deck."})
        return

    issue["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in issue["amount"]]
    change_address = change(utxo)
    ct = pa.CardTransfer(deck, issue["receiver"], issue["amount"])
    raw_ct = hexlify(pa.card_issue(deck, ct, utxo,
                                   change_address
                                   )
                    ).decode()

    signed = provider.signrawtransaction(raw_ct)
    txid = provider.sendrawtransaction(signed["hex"]) # send the tx
    print("\n", txid, "\n")

def card_burn(provider, args):
    '''
    Burn cards of this deck.

    pacli card -burn '{"deck": "deck_id", "amount": ["amount"]}'
    '''

    args = json.loads(args)
    try:
        deck = find_deck(provider, args["deck"])[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    if not provider.getaddressesbyaccount(deck.name):
        print("\n", {"error": "You are not even subscribed to this deck, how can you burn cards?"})
        return

    utxo = provider.select_inputs(0.02)
    change_address = change(utxo)
    issue["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in issue["amount"]]
    cb = pa.CardTransfer(deck, [deck.issuer], args["amount"])
    raw_cb = hexlify(pa.card_burn(deck, cb, utxo,
                                  change_address
                                  )
                    ).decode()

    signed = provider.signrawtransaction(raw_cb)
    print("\n", provider.sendrawtransaction(signed["hex"]), "\n") # send the tx

def card_transfer(provider, args):
    '''
    Transfer cards to <receivers>

    pacli card -transfer '{"deck": "deck_id",
                        "receivers": [list of receiver addresses], "amounts": [list of amounts]
                        }
    '''

    args = json.loads(args)
    try:
        deck = find_deck(provider, args["deck"])[0]
    except IndexError:
        print({"error": "Deck not found!"})
        return
    if not provider.getaddressesbyaccount(deck.name):
        print("\n", {"error": "You are not even subscribed to this deck, how can you transfer cards?"})

    utxo = provider.select_inputs(0.02)
    change_address = change(utxo)
    issue["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in issue["amount"]]
    ct = pa.CardTransfer(deck, args["receiver"], args["amount"])
    raw_ct = hexlify(pa.card_transfer(deck, ct, utxo,
                                      change_address
                                      )
                    ).decode()

    signed = provider.signrawtransaction(raw_ct)
    print("\n", provider.sendrawtransaction(signed["hex"]), "\n") # send the tx

def cli():
    '''CLI arguments parser'''

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
    deck.add_argument("-new", action="store", help="spawn new deck")

    card = subparsers.add_parser('card', help='Cards manipulation.')
    card.add_argument("-list", action="store", help="list all card transactions of this deck.")
    card.add_argument("-issue", action="store", help="issue cards for this deck.")
    card.add_argument("-transfer", action="store", help="send cards to receivers.")
    card.add_argument("-burn", action="store", help="burn cards.")

    return parser.parse_args()

def main():

    first_run()
    load_conf()
    provider = pa.RpcNode(testnet=Settings.testnet)
    set_up(provider)
    args = cli()

    if args.command == "deck":
        if args.list:
            deck_list(provider, args.list)
        if args.subscribe:
            deck_subscribe(provider, args.subscribe)
        if args.search:
            deck_search(provider, args.search)
        if args.info:
            deck_info(provider, args.info)
        if args.new:
            new_deck(provider, args.new)

    if args.command == "card":
        if args.issue:
            card_issue(provider, args.issue)
        if args.burn:
            card_burn(provider, args.burn)
        if args.transfer:
            card_transfer(provider, args.transfer)
        if args.list:
            list_cards(provider, args.list)

if __name__ == "__main__":
    main()
