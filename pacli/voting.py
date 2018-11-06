import pypeerassets as pa
from pypeerassets import voting

from pypeerassets.protocol import Deck

from pacli.config import Settings
from pacli.provider import provider

from pacli.tui import print_vote_list
from prettyprinter import cpprint as pprint

from pacli.utils import (cointoolkit_verify,
                         signtx,
                         sendtx
                         )

from pacli.exceptions import DeckNotFound


class Vote:

    @classmethod
    def _find_deck(self, deckid) -> Deck:

        deck = pa.find_deck(provider, deckid,
                            Settings.deck_version,
                            Settings.production)

        if deck:
            return deck
        else:
            raise DeckNotFound

    def list(self, deckid: str):
        '''find all votes for the deck'''

        deck = self._find_deck(deckid)

        inits = list(voting.find_vote_inits(provider, deck))

        print_vote_list(inits)

    def init(self,
             deckid: str,
             description: str,
             count_mode: int,
             choices: list,
             start: int,
             end: int,
             metainfo: str="",
             version: int=1,
             locktime: int=0,
             send: bool=False,
             verify: bool=False,
             sign: bool=False
             ):

        deck = self._find_deck(deckid)

        vote_init = voting.VoteInit(
            deck=deck,
            count_mode=int(count_mode),
            description=str(description),
            choices=list(choices),
            start_block=int(start),
            end_block=int(end),
            vote_metainfo=str(metainfo),
            version=int(version)
        )

        vi = voting.vote_init(vote_init=vote_init,
                              inputs=provider.select_inputs(Settings.key.address, 0.02),
                              change_address=Settings.change,
                              locktime=0
                              )

        if verify:
            return cointoolkit_verify(vi.hexlify())  # link to cointoolkit - verify

        if sign:

            tx = signtx(vi)

            if send:
                pprint({'txid': sendtx(tx)})

            pprint({'hex': tx.hexlify()})

        return vi.hexlify()
