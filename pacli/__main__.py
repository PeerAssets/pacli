from pacli.config import Settings
import os, argparse
import pypeerassets as pa
from pypeerassets.pautils import exponent_to_amount
from pacli.provider import provider

from pacli.deck import *
from pacli.card import *
from pacli.vote import *

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
        kwargs['keystore'] = keystore = GpgKeystore(Settings)

    provider = Provider(**kwargs)
    set_up(provider)

    return provider


def main():

    provider = configured_provider(Settings)

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
