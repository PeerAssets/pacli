from terminaltables import AsciiTable
from binascii import hexlify
import pypeerassets as pa
from pacli.deck import find_deck 
import json

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


