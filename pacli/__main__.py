import click
from pacli.deck import deck
from pacli.card import card
from pacli.vote import vote
from pacli.top_level_commands import top_level

top_level.add_command(deck)
top_level.add_command(card)
top_level.add_command(vote)

def main():
    top_level()

if __name__ == "__main__":
    main()
