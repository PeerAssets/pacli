import click
from click_default_group import DefaultGroup
from binascii import hexlify
#from pypeerassets import find_card_transfers, find_all_valid_decks, DeckState, Deck, load_deck_p2th_into_local_node
import pypeerassets as pa
import json
from pacli.config import Settings
from pacli.provider import provider, change
from utils import tstamp_to_iso, print_table


def default_account_utxo(amount):
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


def get_state(deck):
    '''return balances of this deck'''

    cards = pa.find_card_transfers(provider, deck)
    if cards:
        return pa.DeckState(cards)
    else:
        raise ValueError("No cards on this deck.")


def deck_title(deck):
    return "Deck id: " + deck.asset_id + " "


def print_deck_info(deck):
    assert isinstance(deck, pa.Deck)
    ## TODO add subscribed column
    heading = ("asset name", "issuer", "issue mode", "decimals", "issue time")
    data = [[
        deck[attr] for attr in 
        ["name", "issuer", "issue_mode", "number_of_decimals", "issue_time"]
        ]]
    print_table(title=deck_title(deck), heading, data)


def print_deck_balances(deck, balances={}):
    '''Show balances of address tied with this deck.'''
    assert isinstance(deck, pa.Deck)
    precision = deck.number_of_decimals
    ## TODO add subscribed column
    heading = ("address", "balance")
    data = [[address, exponent_to_amount(balance, precision)]
            for address, balance in balances]
    print_table(title=deck_title(deck), heading, data)


def deck_summary_line_item(deck):
    d = deck.__dict__
    return [d["asset_id"][:20],
            d["name"],
            d["issuer"],
            d["issue_mode"] ]


def print_deck_list(decks):
    '''Show summary of every deck'''

    decks = list(decks)

    ## TODO add subscribed column
    heading = ("asset ID", "asset name", "issuer", "mode")
    data = map(deck_summary_line_item, list(decks))
    print_table(title="Decks", heading, data)


def search_decks(key: str) -> list:
    '''search decks by <key>'''

    decks = list(pa.find_all_valid_decks(provider, deck_version=Settings.deck_version, prod=Settings.production))
    for i in decks:
        i.short_id = i.asset_id[:20]

    return [d for d in decks if key in d.__dict__.values()]


def find_deck(key: str):
    '''find single deck by <key>'''
    try:
        return search_decks(key)[0]
    except IndexError:
        raise Exception({"error": "Deck not found!"})


def list():
    '''list command'''

    decks = pa.find_all_valid_decks(provider=provider, deck_version=Settings.deck_version,
                                    prod=Settings.production)
    d = ListDecks(decks)
    d.pack_decks_for_printing()
    print(d.table.table)


class SingleDeck:

    def __init__(self, deck_id):
        self.deck = find_deck(deck_id)

    def info(self):
        '''info commands, show full deck details'''
        print_deck_info(deck)

    def balances(self):
        '''show deck balances'''
        print_deck_balances(self.deck, get_state(self.deck).balances)

    def subscribe(self):
        '''subscribe command, load deck p2th into local node>'''
        pa.load_deck_p2th_into_local_node(provider, self.deck)

    def checksum(self):
        ''' verify checksum '''
        if get_state(self.deck).checksum:
            print("\n", "Deck checksum is correct.")
        else:
            print("\n", "Deck checksum is incorrect.")

    @classmethod()
    def options(self, func):
        for option in ['info', 'balances', 'subscribe', 'checksum']:
            func = click.option('--' + option, is_flag=True)(func)
        return func
            


@click.group(cls=DefaultGroup, default='find', default_if_no_args=True)
def deck():
    pass


@deck.command()
@click.argument('deck_id')
@SingleDeck.options
def find(deck_id, **options):
    deck = SingleDeck(deck_id)
    for option in options or ['info']:
        deck[option]()


@deck.command()
@click.argument('deck_id')
def search(deck_id):
    '''search commands, query decks by <deck_id>'''
    print_deck_list(search_decks(deck_id))


@deck.command()
@click.argument('deck')
@click.option('--broadcast/--no-broadcast', default=False)
def new_deck(deck, broadcast):
    '''
    Spawn a new PeerAssets deck.

    pacli deck --new '{"name": "test", "number_of_decimals": 1, "issue_mode": "ONCE"}'

    Will return deck span txid.
    '''

    deck = json.loads(deck)
    deck["network"] = Settings.network
    deck["production"] = Settings.production
    #utxo = provider.select_inputs(0.02)  # we need 0.02 PPC
    utxo = default_account_utxo(0.02)
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
        pa.load_deck_p2th_into_local_node(d) # subscribe to deck
    else:
        print("\nraw transaction:\n", signed["hex"], "\n")


