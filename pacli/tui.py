from terminaltables import AsciiTable
from datetime import datetime
from pypeerassets import Deck, CardTransfer
from pypeerassets.voting import VoteInit
from pypeerassets.pautils import exponent_to_amount


def tstamp_to_iso(tstamp):
    '''make iso timestamp from unix timestamp'''

    return datetime.fromtimestamp(tstamp).isoformat()


def print_table(title, heading, data):
    " prints a table to the terminal using terminaltables.AsciiTable "

    data = list(data)
    data.insert(0, heading)
    table = AsciiTable(data, title=title)
    print(table.table)


def deck_title(deck):
    return "Deck ID: " + deck.id + " "


def deck_summary_line_item(deck: Deck):

    d = deck.__dict__
    return [d["id"],
            d["name"],
            d["issuer"],
            d["issue_mode"],
            d["tx_confirmations"]
            ]


def print_deck_list(decks: list):
    '''Show summary of every deck'''

    print_table(
            title="Decks",
            heading=("ID", "name", "issuer", "mode", "confirms"),
            data=map(deck_summary_line_item, decks))


def print_deck_info(deck: Deck):

    deck.issue_time = tstamp_to_iso(deck.issue_time)
    deck.data = str(deck.asset_specific_data)

    print_table(
            title=deck_title(deck),
            heading=("name", "issuer", "issue mode", "p2th", "decimals", "confirms", "timestamp", "data"),
            data=[[
                getattr(deck, attr) for attr in
                        ["name", "issuer", "issue_mode", "p2th_address",
                         "number_of_decimals", "tx_confirmations",
                         "issue_time", "data"]]]
                         )


def card_line_item(card: CardTransfer):

    c = card.__dict__
    return [c["txid"],
            c["tx_confirmations"],
            c['cardseq'],
            c["sender"],
            c["receiver"][0],
            exponent_to_amount(c["amount"][0], c["number_of_decimals"]),
            c["type"]
            ]


def print_card_list(cards: list):

    print_table(
            title="Card transfers of deck {deck}:".format(deck=cards[0].deck_id),
            heading=("txid", "confirms", "seq", "sender", "receiver", "amount", "type"),
            data=map(card_line_item, cards))


def vote_line_item(vote_init: VoteInit) -> list:

    d = vote_init.__dict__
    return [d["id"],
            d["description"],
            d["sender"],
            tuple(d["choices"]),
            d["count_mode"],
            d["start_block"],
            d["end_block"],
            d["tx_confirmations"]
            ]


def print_vote_list(inits: list):
    '''Show summary of every found VoteInit'''

    print_table(
            title="VoteInits of deck {deck}:".format(
                                                     deck=inits[0].deck.id
                                                     ),
            heading=("ID", "descript", "sender", "choices", "mode", "start",
                     "end", "confirms"),
            data=map(vote_line_item, inits)
            )
