from terminaltables import AsciiTable
import click

from binascii import hexlify
from pacli.provider import provider, change

def tstamp_to_iso(tstamp):
    '''make iso timestamp from unix timestamp'''

    return datetime.fromtimestamp(tstamp).isoformat()

def print_table(title, heading, data):
    " prints a table to the terminal using terminaltables.AsciiTable "
    data = list(data)
    data.insert(0, heading)
    table = AsciiTable(data, title=title)
    print(table.table)


def throw(message):
    raise click.ClickException({ "error": message })


def handle_transaction(transaction, broadcast):
    raw_transaction = hexlify(transaction).decode()
    signed = provider.signrawtransaction(raw_transaction)
    if broadcast:
        txid = provider.sendrawtransaction(signed["hex"])  # send the tx
        print("\n", txid, "\n")
    else:
        print("\nraw transaction:\n", signed["hex"], "\n")

