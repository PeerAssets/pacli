import click
from pacli.export import export_to_csv
from binascii import hexlify
import pypeerassets as pa
from pypeerassets.pautils import amount_to_exponent, exponent_to_amount
from pacli.deck import find_deck 
import json
from pacli.provider import provider, change
from .utils import print_table

def throw(message):
    raise click.ClickException({ "error": message })


def validate_transfer(deck, amounts):
    if not provider.getaddressesbyaccount(deck.name):
        throw("You are not subscribed to this deck")
    try:
        my_balance = get_my_balance(deck.asset_id)
        if not sum(amounts) <= sum(my_balance.values()):
            throw("You don't have enough cards on this deck.")
    except ValueError:
        throw("You have no cards on this deck.")


def _transfer_cards(deck, receivers, amounts, broadcast, utxo):
    change_address = change(utxo)
    ct = pa.CardTransfer(deck=deck, receiver=receivers, amount=amounts)
    raw_ct = hexlify(pa.card_transfer(deck, ct, utxo, change_address)).decode()

    signed = provider.signrawtransaction(raw_ct)

    if broadcast:
        txid = provider.sendrawtransaction(signed["hex"])  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed["hex"], "\n")


def transfer_cards(deck, receivers, amounts, broadcast):

    validate_transfer(deck, amounts)
    utxo = provider.select_inputs(0.02)
    _transfer_cards(deck, receivers, amounts, broadcast, utxo)

def card_line_item(card):
    c = card.__dict__
    return [c["txid"][:20],
            c["sender"],
            c["receiver"][0],
            exponent_to_amount(c["amount"][0], c["number_of_decimals"]),
            c["type"],
            provider.getrawtransaction(card["txid"], 1)["confirmations"] if card["blockhash"] != 0 else 0 ]

def print_card_list(cards):
    ## TODO: add subscribed column
    print_table(
            title="Card transfers of this deck:",
            heading=("txid", "sender", "receiver", "amount", "type", "confirms"),
            data=map(card_line_item, cards))


@click.group()
def card():
    pass


@card.command()
@click.argument('deck_id')
def list(deck_id):
    '''List cards of this <deck>'''
    deck = find_deck(deck_id)

    if isinstance(provider, pa.RpcNode):
        if not provider.getaddressesbyaccount(deck.name):
            print("\n", {"error": "You must subscribe to deck to be able to list transactions."})
            return
    all_cards = pa.find_card_transfers(provider, deck)
    cards = pa.validate_card_issue_modes(deck, all_cards)
    print_card_list(cards)


@card.command()
@click.argument('deck_id')
@click.argument('filename')
def export(deck_id, filename):
    ''' export cards to csv <filename> '''

    deck = find_deck(deck_id)

    if not provider.getaddressesbyaccount(deck.name):
        throw("You must subscribe to deck to be able to list transactions.")

    all_cards = pa.find_card_transfers(provider, deck)
    cards = pa.validate_card_issue_modes(deck, all_cards)

    export_to_csv(cards, filename)


def parse_transfer_json(transfer_json: str) -> dict:
    return json.loads(transfer_json)

@card.command()
@click.argument('issuence', callback=parse_transfer_json)
@click.option('--broadcast/--no-broadcast', default=False)
def issue(issuence, broadcast):
    '''
    Issue new cards of this deck.

    pacli card issue '{"deck": "deck_id",
                        "receivers": [list of receiver addresses],
                        "amounts": [list of amounts]
                        }
    '''

    deck = find_deck(issuence["deck"])

    if not provider.gettransaction(deck.asset_id)["confirmations"] > 0:
        print("\n", "You are trying to issue cards on a deck which has not been confirmed yet.")

    if provider.validateaddress(deck.issuer)["ismine"]:
        try:
            utxo = provider.select_inputs(0.02, deck.issuer)
        except ValueError:
            throw("Please send funds to the deck issuing address: {0}".format(deck.issuer))
    else:
        raise throw("You are not the owner of this deck.")

    issuence["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in issuence["amount"]]
    _transfer_cards(deck, receivers=issuence["receiver"], amounts=issuence["amount"], broadcast=broadcast, utxo=utxo)


@card.command()
@click.argument('deck_id')
@click.argument('burn_order', callback=parse_transfer_json)
@click.option('--broadcast/--no-broadcast', default=False)
def burn(burn_order, broadcast):
    '''
    Burn cards of this deck.

    pacli card burn <deck_id> amount_one, amount_two...
    '''

    deck = find_deck(burn_order['deck'])
    amounts = [amount_to_exponent(float(i), deck.number_of_decimals) for i in burn_order['amounts']]
    transfer_cards(deck, [deck.issuer], amounts, broadcast)


@card.command()
@click.argument('transfer_order', callback=parse_transfer_json)
@click.option('--broadcast/--no-broadcast', default=False)
def transfer(transfer_order, broadcast):
    '''
    Transfer cards to <receivers>

    pacli card -transfer '{"deck": "deck_id",
                        "receivers": [list of receiver addresses], "amounts": [list of amounts]
                        }
    '''

    deck = find_deck(transfer_order["deck"])
    transfer_order["amount"] = [amount_to_exponent(float(i), deck.number_of_decimals) for i in transfer_order["amount"]]
    transfer_cards(deck, transfer_order["receiver"], transfer_order["amount"], broadcast)


