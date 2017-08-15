import click
import pypeerassets as pa
import json
from pacli.config import Settings
from pacli.provider import provider, change

@click.group()
def top_level():
    '''Simple CLI PeerAssets client.'''
    pass

@top_level.command()
@click.argument('deck_id')
@click.argument('address')
def address_balance(deck_id, address):
    '''show card balance of the address'''

    deck = find_deck(deck_id)
    balances = get_state(deck).balances

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


def get_my_balance(deck_id):
    '''get balances on the deck owned by me'''

    deck = find_deck(deck_id)

    my_addresses = provider.getaddressesbyaccount()
    deck_balances = get_state(deck).balances
    matches = list(set(my_addresses).intersection(deck_balances))

    return {i: deck_balances[i] for i in matches if i in deck_balances.keys()}


@top_level.command()
def status():
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
            my_balances = get_my_balance(deck["deck_id"])
            deck["balance"] = exponent_to_amount(sum(my_balances.values()),
                                                 deck["number_of_decimals"])
            deck["address_handle"] = list(my_balances.keys())[0]  # show address which handles this deck, first one only though
            deck.pop("number_of_decimals")  # this should not go into report
        except:
            deck.pop("number_of_decimals")  # this should not go into report
            deck["balance"] = 0

    return report


@top_level.command()
def new_address():
    '''generate a new address and import into wallet.'''

    key = pa.Kutil(network=provider.network)
    provider.importprivkey(key.wif, "PACLI")
    return key.address
