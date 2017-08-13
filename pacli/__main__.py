from datetime import datetime
from terminaltables import AsciiTable
from binascii import hexlify
from appdirs import user_config_dir
from pacli.config import write_default_config, read_conf
from pacli.export import export_to_csv
import os, argparse
import pypeerassets as pa
from pypeerassets.pautils import amount_to_exponent, exponent_to_amount
import json
import logging

from pacli.keystore import GpgKeystore, as_local_key_provider

conf_dir = user_config_dir("pacli")
conf_file = os.path.join(conf_dir, "pacli.conf")
logfile = os.path.join(conf_dir, "pacli.log")
keyfile = os.path.join(conf_dir, "pacli.gpg")

class Settings:
    pass


def load_conf():
    '''load user configuration'''

    settings = read_conf(conf_file)

    for key in settings:
        setattr(Settings, key, settings[key])

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
    if not os.path.exists(keyfile):
        open(keyfile, 'a').close()

def set_up(provider):
    '''setup'''

    # if provider is local node, check if PA P2TH is loaded in local node
    # this handles indexing of transaction
    if Settings.provider == "rpcnode":
        if Settings.production:
            if not provider.listtransactions("PAPROD"):
                pa.pautils.load_p2th_privkeys_into_local_node(provider)
        if not Settings.production:
            if not provider.listtransactions("PATEST"):
                pa.pautils.load_p2th_privkeys_into_local_node(provider, prod=False)
   #elif Settings.provider != 'holy':
   #    pa.pautils.load_p2th_privkeys_into_local_node(provider, keyfile)

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

    decks = list(pa.find_all_valid_decks(provider, deck_version=Settings.deck_version, prod=Settings.production))
    for i in decks:
        i.short_id = i.asset_id[:20]

    return [d for d in decks if key in d.__dict__.values()]


class ListDecks:

    @classmethod
    def __init__(cls, provider, decks):
        cls.provider = provider
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

class ListCards:

    @classmethod
    def __init__(cls, provider, cards):
        cls.provider = provider
        cls.cards = list(cards)

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
            l.append(cls.provider.getrawtransaction(card["txid"], 1)["confirmations"])
        else:
            l.append(0)

        return l

    @classmethod
    def pack_cards_for_printing(cls):

        #assert len(cls.cards) > 0, {"error": "No cards found!"}

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


def deck_list(provider):
    '''list command'''

    d = ListDecks(provider, pa.find_all_valid_decks(provider, 
                  Settings.deck_version, Settings.production))
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
    if isinstance(provider, pa.RpcNode):
        if not provider.getaddressesbyaccount(deck.name):
            print("\n", {"error": "You must subscribe to deck to be able to list transactions."})
            return

    all_cards = pa.find_card_transfers(provider, deck)
    cards = pa.validate_card_issue_modes(deck, all_cards)
    c = ListCards(provider, cards)
    c.pack_cards_for_printing()
    print(c.table.table)


def export_cards(provider, args):
    '''
    export cards to csv <filename>

    pacli card -export <deck> filename
    '''

    try:
        deck = find_deck(provider, args[0])[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    if not provider.getaddressesbyaccount(deck.name):
        print("\n", {"error": "You must subscribe to deck to be able to list transactions."})
        return

    all_cards = pa.find_card_transfers(provider, deck)
    cards = pa.validate_card_issue_modes(deck, all_cards)

    export_to_csv(cards, args[1])


def card_issue(provider, args, broadcast):
    '''
    Issue new cards of this deck.

    pacli card -issue '{"deck": "deck_id",
                        "receivers": [list of receiver addresses],
                        "amounts": [list of amounts]
                        }
    '''

    issue = json.loads(args)
    try:
        deck = find_deck(provider, issue["deck"])[0]
    except IndexError:
        print("\n", {"error": "Deck not found."})
        return

    if not provider.gettransaction(deck.asset_id)["confirmations"] > 0:
        print("\n", "You are trying to issue cards on a deck which has not been confirmed yet.")

    if provider.validateaddress(deck.issuer)["ismine"]:
            try:
                utxo = provider.select_inputs(0.02, deck.issuer)
            except ValueError:
                print("\n", {"error": "Please send funds to the deck issuing address: {0}".format(deck.issuer)})
                return
    else:
        print("\n", {"error": "You are not the owner of this deck."})
        return

    issue["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in issue["amount"]]
    change_address = change(utxo)
    ct = pa.CardTransfer(deck=deck, receiver=issue["receiver"],
                         amount=issue["amount"])
    raw_ct = hexlify(pa.card_issue(deck, ct, utxo,
                                   change_address
                                   )
                     ).decode()

    signed = provider.signrawtransaction(raw_ct)

    if broadcast:
        txid = provider.sendrawtransaction(signed["hex"])  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed["hex"], "\n")


def card_burn(provider, args, broadcast):
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
    try:
        my_balance = get_my_balance(provider, deck.asset_id)
    except ValueError:
        print("\n", {"error": "You have no cards on this deck."})
        return

    args["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in args["amount"]]
    assert sum(args["amount"]) <= sum(my_balance.values()), {"error": "You don't have enough cards on this deck."}

    utxo = provider.select_inputs(0.02)
    change_address = change(utxo)
    cb = pa.CardTransfer(deck=deck, receiver=[deck.issuer], amount=args["amount"])
    raw_cb = hexlify(pa.card_burn(deck, cb, utxo,
                                  change_address
                                  )
                     ).decode()

    signed = provider.signrawtransaction(raw_cb)

    if broadcast:
        txid = provider.sendrawtransaction(signed["hex"])  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed["hex"], "\n")


def card_transfer(provider, args, broadcast):
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
    try:
        my_balance = get_my_balance(provider, deck.asset_id)
    except ValueError:
        print("\n", {"error": "You have no cards on this deck."})
        return

    args["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in args["amount"]]
    assert sum(args["amount"]) <= sum(my_balance.values()), {"error": "You don't have enough cards on this deck."}

    utxo = provider.select_inputs(0.02)
    change_address = change(utxo)
    ct = pa.CardTransfer(deck=deck, receiver=args["receiver"], amount=args["amount"])
    raw_ct = hexlify(pa.card_transfer(deck, ct, utxo,
                                      change_address
                                      )
                     ).decode()

    signed = provider.signrawtransaction(raw_ct)

    if broadcast:
        txid = provider.sendrawtransaction(signed["hex"])  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed["hex"], "\n")


def get_state(provider, deck):
    '''return balances of this deck'''

    cards = pa.find_card_transfers(provider, deck)
    if cards:
        return pa.DeckState(cards)
    else:
        raise ValueError("No cards on this deck.")


def get_my_balance(provider, deck_id):
    '''get balances on the deck owned by me'''

    try:
        deck = find_deck(provider, deck_id)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})

    my_addresses = provider.getaddressesbyaccount()
    deck_balances = get_state(provider, deck).balances
    matches = list(set(my_addresses).intersection(deck_balances))

    return {i: deck_balances[i] for i in matches if i in deck_balances.keys()}


def address_balance(provider, deck_id, address):
    '''show deck balances'''

    try:
        deck = find_deck(provider, deck_id)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    balances = get_state(provider, deck).balances
    try:
        b = exponent_to_amount(balances[address], deck.number_of_decimals)
    except:
        print("\n", {"error": "This address has no card balance."})
        return

    print("\n", "Card balance: {balance}".format(balance=b), "\n")


def subscribed_decks(provider):
    '''find subscribed-to decks'''

    decks = pa.find_all_valid_decks(provider)
    for i in decks:
        if provider.getaddressesbyaccount(i.name):
            yield i


def status(provider):
    '''show status of this pacli instance'''

    report = {}
    report["network"] = provider.network
    report["subscribed_decks"] = []
    for i in list(subscribed_decks(provider)):
        report["subscribed_decks"].append({
            "deck_name": i.name,
            "deck_id": i.asset_id,
            "number_of_decimals": i.number_of_decimals
        })
    for deck in report["subscribed_decks"]:
        try:
            my_balances = get_my_balance(provider, deck["deck_id"])
            deck["balance"] = exponent_to_amount(sum(my_balances.values()),
                                                 deck["number_of_decimals"])
            deck["address_handle"] = list(my_balances.keys())[0]  # show address which handles this deck, first one only though
            deck.pop("number_of_decimals")  # this should not go into report
        except:
            deck.pop("number_of_decimals")  # this should not go into report
            deck["balance"] = 0

    return report


def new_address(provider):
    '''generate new address and import into wallet.'''

    key = pa.Kutil(network=provider.network)
    provider.importprivkey(key.wif, "PACLI")
    return key.address

## Voting #

def new_vote(provider, args, broadcast):
    '''
    Initialize new vote on the <deck>

    pacli vote --new <deck> '{"choices": ["y", "n"], "count_mode": "SIMPLE",
    "description": "test", "start_block": int, "end_block": int}'
    '''

    try:
        deck = find_deck(provider, args[0])[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return

    args = json.loads(args[1])
    inputs = provider.select_inputs(0.02)
    change_address = change(inputs)
    vote = pa.Vote(version=1, deck=deck, **args)

    raw_vote_init = hexlify(pa.vote_init(vote, inputs, change_address)).decode()
    signed = provider.signrawtransaction(raw_vote_init)["hex"]

    if broadcast:
        txid = provider.sendrawtransaction(signed)  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed, "\n")


def vote_cast(provider, args, broadcast):
    '''
    cast a vote
    args = deck, vote_id, choice
    '''

    try:
        deck = find_deck(provider, args[0])[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return

    for i in pa.find_vote_inits(provider, deck):
        if i.vote_id == args[1]:
            vote = i

    if not vote:
        return {"error": "Vote not found."}
    if isinstance(args[2], int):
        choice = args[2]
    else:
        choice = list(vote.choices).index(args[2])
    inputs = provider.select_inputs(0.02)
    change_address = change(inputs)
    cast = pa.vote_cast(vote, choice, inputs, change_address)

    raw_vote_cast = hexlify(cast).decode()
    signed = provider.signrawtransaction(raw_vote_cast)["hex"]

    if broadcast:
        txid = provider.sendrawtransaction(signed)  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed, "\n")


class ListVotes:

    @classmethod
    def __init__(cls, provider, votes):
        cls.provider = provider
        cls.votes = list(votes)

        ## Vote table header
        cls.vote_table = [
            ## add subscribed column
            ("vote_id", "sender", "description", "start_block", "end_block")
        ]

        cls.table = AsciiTable(cls.vote_table, title="Votes on this deck:")

    @classmethod
    def dtl(cls, vote, subscribed=False):
        '''votes-to-list: votes to table-printable list'''

        l = []
        l.append(vote["vote_id"])
        l.append(vote["sender"])
        l.append(vote["description"])
        l.append(vote["start_block"])
        l.append(vote["end_block"])

        return l

    @classmethod
    def pack_for_printing(cls):

        for i in cls.votes:
            cls.vote_table.append(
                cls.dtl(i.__dict__)
            )


def list_votes(provider, args):
    '''list all votes on the <deck>'''

    try:
        deck = find_deck(provider, args)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    vote_inits = list(pa.find_vote_inits(provider, deck))

    c = ListVotes(provider, vote_inits)
    c.pack_for_printing()
    print(c.table.table)


def vote_info(provider, args):
    '''show detail information about <vote> on the <deck>'''

    try:
        deck = find_deck(provider, args[0])[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return

    for i in pa.find_vote_inits(provider, deck):
        if i.vote_id == args[1]:
            vote = i

    vote.deck = vote.deck.asset_id
    print("\n", vote.__dict__)
    return


def cli():
    '''CLI arguments parser'''

    parser = argparse.ArgumentParser(description='Simple CLI PeerAssets client.')
    subparsers = parser.add_subparsers(title="Commands",
                                       dest="command",
                                       description='valid subcommands')

    parser.add_argument("--broadcast", action="store_true", help="broadcast resulting transactions")
    parser.add_argument("--newaddress", action="store_true",
                        help="generate a new address and import to wallet")
    parser.add_argument("--status", action="store_true", help="show pacli status")
    parser.add_argument("--addressbalance", action="store",
            metavar=('DECK_ID', 'ADDRESS'), nargs=2, help="check card balance of the address")

    deck = subparsers.add_parser('deck', help='Deck manipulation.')
    deck.add_argument("--list", action="store_true", help="list decks")
    deck.add_argument("--info", action="store", help="show details of <asset_id>")
    deck.add_argument("--subscribe", action="store", help="subscribe to <deck id>")
    deck.add_argument("--search", action="store", help='''search for decks by name, id,
                       issue mode, issuer or number of decimals''')
    deck.add_argument("--new", action="store", help="spawn new deck")
    deck.add_argument("--checksum", action="store", help="verify deck card balance checksum")
    deck.add_argument("--balances", action="store", help="show balances of this deck")

    card = subparsers.add_parser('card', help='Card manipulation.')
    card.add_argument("--list", action="store", help="list all card transactions of this deck")
    card.add_argument("--export", action="store", nargs=2, help="export all cards of this deck to csv file")
    card.add_argument("--issue", action="store", help="issue cards for this deck")
    card.add_argument("--transfer", action="store", help="send cards to receivers")
    card.add_argument("--burn", action="store", help="burn cards")

    vote = subparsers.add_parser('vote', help='Vote manipulation.')
    vote.add_argument("--list", action="store", help="List all vote transactions of this deck")
    vote.add_argument("--new", action="store", nargs=2, help="Initiate new vote or poll.")
    vote.add_argument("--cast", action="store", help="Cast a vote.")
    vote.add_argument("--info", action="store", nargs=2, help="Information about vote.")

    return parser.parse_args()


def configured_provider(Settings):
    " resolve settings into configured provider "

    if Settings.provider.lower() == "rpcnode":
        Provider = pa.RpcNode
        kwargs = dict(testnet=Settings.testnet)

    elif Settings.provider.lower() == "holy":
        Provider = pa.Holy
        kwargs = dict(network=Settings.network)

    elif Settings.provider.lower() == "cryptoid":
        Provider = pa.Cryptoid
        kwargs = dict(network=Settings.network)

    else:
        raise Exception('invalid provider')

    if Settings.keystore.lower() == "gnupg":
        Provider = as_local_key_provider(Provider)
        kwargs['keystore'] = keystore = GpgKeystore(Settings, keyfile)

    provider = Provider(**kwargs)
    set_up(provider)

    return provider


def main():

    first_run()
    load_conf()

    provider = configured_provider(Settings)

    args = cli()

    if args.status:
        print(json.dumps(status(provider), indent=4))

    if args.newaddress:
        print("\n", new_address(provider))

    if args.addressbalance:
        address_balance(provider, args.addressbalance[0], args.addressbalance[1])

    if args.command == "deck":
        if args.list:
            deck_list(provider)
        if args.subscribe:
            deck_subscribe(provider, args.subscribe)
        if args.search:
            deck_search(provider, args.search)
        if args.info:
            deck_info(provider, args.info)
        if args.new:
            new_deck(provider, args.new, args.broadcast)
        if args.checksum:
            deck_checksum(provider, args.checksum)
        if args.balances:
            deck_balances(provider, args.balances)

    if args.command == "card":
        if args.issue:
            card_issue(provider, args.issue, args.broadcast)
        if args.burn:
            card_burn(provider, args.burn, args.broadcast)
        if args.transfer:
            card_transfer(provider, args.transfer, args.broadcast)
        if args.list:
            list_cards(provider, args.list)
        if args.export:
            export_cards(provider, args.export)

    if args.command == "vote":
        if args.new:
            new_vote(provider, args.new, args.broadcast)
        if args.list:
            list_votes(provider, args.list)
        if args.cast:
            vote_cast(provider, args.cast)
        if args.info:
            vote_info(provider, args.info)

    if (hasattr(provider, 'keystore')):
        # could possibly make this direct behavior of dumprivkeys
        provider.keystore.write(provider.dumpprivkeys())
 
if __name__ == "__main__":
    main()
