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
            asset_specific_data: bytes=None, json: bool=False):
        '''create a new deck, print out a protobuf'''

        network = Settings.network
        production = Settings.production
        version = Settings.deck_version

        new_deck = pa.Deck(name, number_of_decimals, issue_mode, network,
                           production, version, asset_specific_data)

        if json:
            return new_deck.metainfo_to_dict

        return new_deck.metainfo_to_protobuf.hex()

    @classmethod
    def decode(self, protobuf: str) -> dict:
        '''decode deck protobuf'''

        return pa.parse_deckspawn_metainfo(bytes.fromhex(protobuf), Settings.deck_version)


class Card:

    '''card information and manipulation'''

    @classmethod
    def list(self, deck_id: str):
        '''list the valid cards on this deck'''

        deck = pa.find_deck(provider, deck_id,
                            Settings.deck_version,
                            Settings.production)

        try:
            cards = list(pa.find_card_transfers(provider, deck))
            return [i.__dict__ for i in cards]
        except pa.exceptions.EmptyP2THDirectory as err:
            return err


def main():

    fire.Fire({
        'deck': Deck(),
        'card': Card()
        })


if __name__ == '__main__':
    main()
