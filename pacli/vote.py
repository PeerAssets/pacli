import click
from terminaltables import AsciiTable
from binascii import hexlify
import pypeerassets as pa
from pacli.deck import find_deck 
import json
from pacli.provider import provider
from .utils import print_table

def throw(message):
    raise click.ClickException({ "error": message })

def handle_transaction(data, broadcast):
    signed = provider.signrawtransaction(hexlify(data).decode())["hex"]

    if broadcast:
        txid = provider.sendrawtransaction(signed)  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed, "\n")

def vote_line_item(vote):
    v= vote.__dict__
    return [v[attr] for attr in
            ["name", "issuer", "issue_mode", "number_of_decimals", "issue_time"]]

def print_vote_list(votes):
    ## TODO: add subscribed column
    print_table(
            title="Votes on this deck:",
            heading=("vote_id", "sender", "description", "start_block", "end_block"),
            data=map(vote_line_item, votes))

@click.group()
def vote():
    pass

@vote.command()
@click.argument('deck_id')
def list_votes(deck_id):
    '''list all votes on the <deck>'''
    votes = list(pa.find_vote_inits(provider, find_deck(deck_id)))
    print_vote_list(votes)

@vote.command()
@click.argument('deck_id')
@click.argument('new_vote')
@click.option('--broadcast/--no-broadcast', default=False)
def new(deck_id, vote_json, broadcast):
    '''
    Initialize new vote on the <deck>

    pacli vote --new <deck> '{"choices": ["y", "n"], "count_mode": "SIMPLE",
    "description": "test", "start_block": int, "end_block": int}'
    '''
    deck = find_deck(deck_id)
    vote_order = json.loads(vote_json)

    inputs = provider.select_inputs(0.02)
    change_address = change(inputs)
    vote = pa.Vote(version=1, deck=deck, **vote_order)

    handle_transaction(pa.vote_init(vote, inputs, change_address), broadcast)


@vote.command()
@click.argument('deck_id')
@click.argument('vote_id')
@click.argument('choice')
def cast(deck_id, vote_id, choice, broadcast):
    '''
    cast a vote
    args = deck, vote_id, choice
    '''
    deck = find_deck(deck)

    for i in pa.find_vote_inits(provider, deck):
        if i.vote_id == vote_id:
            vote = i
    if not vote:
        throw("Vote not found.")

    choice = choice if isinstance(choice, int) else list(vote.choices).index(choice)
    inputs = provider.select_inputs(0.02)
    change_address = change(inputs)
    cast = pa.vote_cast(vote, choice, inputs, change_address)
    handle_transaction(cast, broadcast)


@vote.command()
@click.argument('deck_id')
def info(deck_id):
    '''show detail information about <vote> on the <deck>'''

    deck = find_deck(deck_id)

    for i in pa.find_vote_inits(provider, deck):
        if i.vote_id == args[1]:
            vote = i

    vote.deck = vote.deck.asset_id
    print("\n", vote.__dict__)


