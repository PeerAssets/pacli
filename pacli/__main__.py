import fire
import pypeerassets as pa
from pacli.provider import provider
from pacli.config import Settings


class Deck:

    @classmethod
    def list(self):
        '''find all valid decks and list them.'''

        decks = list(pa.find_all_valid_decks(provider, Settings.deck_version,
                                             Settings.production))

        return decks

    @classmethod
    def find(self, key):
        '''
        Find specific deck by key, with key being:
        <id>, <name>, <issuer>, <issue_mode>, <number_of_decimals>
        '''

        decks = pa.find_all_valid_decks(provider,
                                        Settings.deck_version,
                                        Settings.production)
        return [d for d in decks if key in d.__dict__.values()]

    @classmethod
    def new(self, name: str, number_of_decimals: int, issue_mode: int,
            asset_specific_data: bytes=None):
        '''create a new deck.'''

        network = Settings.network
        production = Settings.production
        version = Settings.version

        new_deck = pa.Deck(name, number_of_decimals, issue_mode, network,
                           production, version, asset_specific_data)

        pa.deck_spawn(provider, Settings.key, new_deck, Settings.change)


def main():

    fire.Fire({
        'deck': Deck()
        })


if __name__ == '__main__':
    main()
