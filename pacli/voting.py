import pypeerassets as pa
from pypeerassets import voting

from pypeerassets.protocol import Deck

from pacli.config import Settings
from pacli.provider import provider

from pacli.tui import print_vote_list


class Vote:

    @classmethod
    def _find_deck(self, deckid) -> Deck:

        deck = pa.find_deck(provider, deckid,
                            Settings.deck_version,
                            Settings.production)

        if deck:
            return deck

    def list(self, deckid: str):
        '''find all votes for the deck'''

        deck = self._find_deck(deckid)

        inits = list(voting.find_vote_inits(provider, deck))

        print_vote_list(inits)
