import fire
import pypeerassets as pa
from pacli.provider import provider
from pacli.config import Settings
from pacli.keystore import init_keystore


def cointoolkit_verify(hex: str) -> str:
    '''tailor cointoolkit verify URL'''

    base_url = 'https://indiciumfund.github.io/cointoolkit/'
    if provider.network == "peercoin-testnet":
        mode = "mode=peercoin_testnet"
    if provider.network == "peercoin":
        mode = "mode=peercoin"

    return base_url + "?" + mode + "&" + "verify=" + hex


class Address:

    '''my personal address'''

    def show(self, pubkey: bool=False, privkey: bool=False, wif: bool=False):
        '''print address, pubkey or privkey'''

        if pubkey:
            return Settings.key.pubkey
        if privkey:
            return Settings.key.privkey
        if wif:
            return Settings.key.wif

        return Settings.key.address


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
        version = Settings.deck_version

        new_deck = pa.Deck(name, number_of_decimals, issue_mode, network,
                           production, version, asset_specific_data)

        return new_deck

    @classmethod
    def spawn(self, verify=False, **kwargs):
        '''prepare deck spawn transaction'''

        deck = self.new(**kwargs)

        spawn = pa.deck_spawn(provider=provider, key=Settings.key,
                              inputs=provider.select_inputs(Settings.key.address, 0.02),
                              deck=deck,
                              change_address=Settings.change
                              )

        if verify:
            return cointoolkit_verify(spawn)  # link to cointoolkit - verify

        return spawn

    @classmethod
    def encode(self, json: bool=False, **kwargs) -> str:
        '''compose a new deck and print out the protobuf which
           is to be manually inserted in the OP_RETURN of the transaction.'''

        if json:
            return self.new(**kwargs).metainfo_to_dict

        return self.new(**kwargs).metainfo_to_protobuf.hex()

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

    def balances(self, deck_id):
        '''list card balances on this deck'''
        raise NotImplementedError

    def new(self, deck_id: str, receivers: list=None, amount: list=None):
        '''fabricate a new card transaction
        * deck_id - deck in question
        * receiver - list of receivers
        * amount - list of amounts to be sent, must be float
        '''
        raise NotImplementedError


def main():

    init_keystore()

    fire.Fire({
        'deck': Deck(),
        'card': Card(),
        'address': Address()
        })


if __name__ == '__main__':
    main()
