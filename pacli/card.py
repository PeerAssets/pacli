from pacli.export import export_to_csv
from terminaltables import AsciiTable
from binascii import hexlify
import pypeerassets as pa
from pypeerassets.pautils import amount_to_exponent, exponent_to_amount
from pacli.deck import find_deck 
import json
from pacli.provider import provider

class ListCards:

    @classmethod
    def __init__(cls, cards):
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


def list_cards(deck_key):
    '''
    List cards of this <deck>.abs

    pacli card -list <deck>
    '''
    try:
        deck = find_deck(deck_key)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    if isinstance(provider, pa.RpcNode):
        if not provider.getaddressesbyaccount(deck.name):
            print("\n", {"error": "You must subscribe to deck to be able to list transactions."})
            return

    all_cards = pa.find_card_transfers(provider, deck)
    cards = pa.validate_card_issue_modes(deck, all_cards)
    c = ListCards(cards)
    c.pack_cards_for_printing()
    print(c.table.table)


def export_cards(args):
    '''
    export cards to csv <filename>

    pacli card -export <deck> filename
    '''

    try:
        deck = find_deck(args[0])[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    if not provider.getaddressesbyaccount(deck.name):
        print("\n", {"error": "You must subscribe to deck to be able to list transactions."})
        return

    all_cards = pa.find_card_transfers(provider, deck)
    cards = pa.validate_card_issue_modes(deck, all_cards)

    export_to_csv(cards, args[1])


def card_issue(args, broadcast):
    '''
    Issue new cards of this deck.

    pacli card -issue '{"deck": "deck_id",
                        "receivers": [list of receiver addresses],
                        "amounts": [list of amounts]
                        }
    '''

    issue = json.loads(args)
    try:
        deck = find_deck(issue["deck"])[0]
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


def card_burn(args, broadcast):
    '''
    Burn cards of this deck.

    pacli card -burn '{"deck": "deck_id", "amount": ["amount"]}'
    '''

    args = json.loads(args)
    try:
        deck = find_deck(args["deck"])[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})
        return
    if not provider.getaddressesbyaccount(deck.name):
        print("\n", {"error": "You are not even subscribed to this deck, how can you burn cards?"})
        return
    try:
        my_balance = get_my_balance(deck.asset_id)
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


def card_transfer(args, broadcast):
    '''
    Transfer cards to <receivers>

    pacli card -transfer '{"deck": "deck_id",
                        "receivers": [list of receiver addresses], "amounts": [list of amounts]
                        }
    '''

    args = json.loads(args)
    try:
        deck = find_deck(args["deck"])[0]
    except IndexError:
        print({"error": "Deck not found!"})
        return
    if not provider.getaddressesbyaccount(deck.name):
        print("\n", {"error": "You are not even subscribed to this deck, how can you transfer cards?"})
    try:
        my_balance = get_my_balance(deck.asset_id)
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


