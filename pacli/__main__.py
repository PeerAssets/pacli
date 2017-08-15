from pacli.config import Settings
import os, argparse
import pypeerassets as pa
from pypeerassets.pautils import exponent_to_amount
from pacli.provider import provider

from pacli.deck import deck
from pacli.card import card
from pacli.vote import vote

def get_my_balance(deck_id):
    '''get balances on the deck owned by me'''

    try:
        deck = find_deck(deck_id)[0]
    except IndexError:
        print("\n", {"error": "Deck not found!"})

    my_addresses = provider.getaddressesbyaccount()
    deck_balances = get_state(deck).balances
    matches = list(set(my_addresses).intersection(deck_balances))

    return {i: deck_balances[i] for i in matches if i in deck_balances.keys()}


def address_balance(deck_id, address):
    '''show deck balances'''

    try:
        deck = find_deck(deck_id)[0]
    except IndexError: print("\n", {"error": "Deck not found!"}) return
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
            my_balances = get_my_balance(deck["deck_id"])
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


def main():

    args = cli()

    if args.status:
        print(json.dumps(status(provider), indent=4))

    if args.newaddress:
        print("\n", new_address(provider))

    if args.addressbalance:
        address_balance(args.addressbalance[0], args.addressbalance[1])

    if args.command == "deck":
        if args.list:
            deck_list(Settings)
        if args.subscribe:
            deck_subscribe(args.subscribe)
        if args.search:
            deck_search(args.search)
        if args.info:
            deck_info(args.info)
        if args.new:
            new_deck(args.new, args.broadcast)
        if args.checksum:
            deck_checksum(args.checksum)
        if args.balances:
            deck_balances(args.balances)

    if args.command == "card":
        if args.issue:
            card_issue(args.issue, args.broadcast)
        if args.burn:
            card_burn(args.burn, args.broadcast)
        if args.transfer:
            card_transfer(args.transfer, args.broadcast)
        if args.list:
            list_cards(args.list)
        if args.export:
            export_cards(args.export)

    if args.command == "vote":
        if args.new:
            new_vote(args.new, args.broadcast)
        if args.list:
            list_votes(args.list)
        if args.cast:
            vote_cast(args.cast)
        if args.info:
            vote_info(args.info)

    if (hasattr(provider, 'keystore')):
        # could possibly make this direct behavior of dumprivkeys
        provider.keystore.write(provider.dumpprivkeys())
 
if __name__ == "__main__":
    main()
