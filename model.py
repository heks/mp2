import logging
import os

from google.appengine.ext import ndb


class Player(ndb.Model):
    game_id = ndb.IntegerProperty()
    player_id = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    tokens = ndb.IntegerProperty()
    cards_visible = ndb.StringProperty(repeated=True)
    cards_not_visible = ndb.StringProperty(repeated=True)

class GameStatus(ndb.Model):
    your_actions = ndb.StringProperty()
    your_cards_visible = ndb.StringProperty(repeated=True)

class Game(ndb.Model):
    name = ndb.StringProperty(required=True)
    players_max = ndb.IntegerProperty()
    players_current = ndb.IntegerProperty()
    deck = ndb.StringProperty(repeated=True)
    common_cards_visible = ndb.StringProperty(repeated=True)
    players = ndb.LocalStructuredProperty(Player, repeated=True)
    current_turn = ndb.StringProperty()
