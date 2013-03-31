import random
import webapp2
import jinja2
import os
import logging
import json
import re

from google.appengine.api import channel

from webapp2_extras import routes
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import ndb
from cors.cors_application import CorsApplication
from cors.cors_options import CorsOptions
from model import Game, Player, GameStatus

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


#52 deck of cards
init_deck = {"2h","3h","4h","5h",'6h','7h','8h','9h','10h','Jh','Qh','Kh','Ah',
              "2d","3d","4d","5d",'6d','7d','8d','9d','10d','Jd','Qd','Kd','Ad',
              "2c","3c","4c","5c","6c",'7c','8c','9c','10c','Jc','Qc','Kc','Ac',
              "2s","3s","4s","5s","6s",'7s','8s','9s','10s','Js','Qs','Ks','As'}

class GameUpdater():
  game = None

  def __init__(self, game):
    self.game = game

  def init_deck(self):
    self.game.deck = init_deck;
    random.shuffle(self.game.deck)
    self.game.common_cards_visible.append(self.game.deck.pop(0))

  def deal_cards(self):
    first_card = self.game.deck.pop(0)
    second_card = self.game.deck.pop(0)
    return [first_card,second_card]

  def draw(self,player):
    player.cards_visible.append(self.game.deck.pop(0))
    player.put()
    self.game.put()
    if self.count(player.cards_visible) > 21:
      return "Busted"
    elif self.count(player.cards_visible) == 21:
      return "Win"
    else:
      return "Cards"

  def count(self, cards):
    total_player = 0
    for card in cards:
      match = re.search(r"\d+", card)
      if match:
        total_player += int(match.group())
      else:
        match = re.search(r"[JQK]", card)
        if match:
          total_player += 10
        else:
          if(total_player <= 10):
            total_player += 11
          else:
            total_player += 1
    return total_player

  def play(self, player, bet):
    total_player = 0
    total_dealer = 0
    for card in player.cards_visible:
      match = re.search(r"\d+", card)
      if match:
        total_player += int(match.group())
      else:
        match = re.search(r"[JQK]", card)
        if match:
          total_player += 10
        else:
          if(total_player <= 10):
            total_player += 11
          else:
            total_player += 1

    self.game.common_cards_visible.append(self.game.deck.pop(0))
    for i,card in enumerate(self.game.common_cards_visible):
      match = re.search(r"\d+", card)
      if match:
        total_dealer += int(match.group())
      else:
        match = re.search(r"[JQK]", card)
        if match:
          total_dealer += 10
        else:
          if(total_dealer <= 10):
            total_dealer += 11
          else:
            total_dealer += 1
      if(total_dealer < 17 and i == len(self.game.common_cards_visible)-1 ):
        self.game.common_cards_visible.append(self.game.deck.pop(0))

    if(total_player == 21 or total_player >= total_dealer or total_dealer > 21):
      player.tokens += bet; 
      self.game.put()
      player.put()
      return "You won" + str(bet) + "tokens"
    else:
      player.tokens -= bet;
      self.game.put()
      player.put()
      return "You lost" + str(bet) + "tokens"



class MainHandler(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>) <a href=\game\> Play Game</a>)" %
                        (user.nickname(), users.create_logout_url("/")))
    else:
      greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/"))

    self.response.out.write("<html><body>%s</body></html>" % greeting)

class GameHandler(webapp2.RequestHandler):

  def get(self):
    template = jinja_environment.get_template('main.html')

    games = ndb.gql('SELECT * From Game')
    values = {
        'games' : games
    }


    self.response.out.write(
        template.render(values)
    )
    
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect_to('/')
    name = self.request.get('game_name')
    new_game = Game(
        name = name,
        players_max = 6,
        players_current = 0,
    )
    GameUpdater(new_game).init_deck()
    new_game.put()

    self.redirect_to('player',game_id=new_game.key.id())

class ActionHandler(webapp2.RequestHandler):
  def post(self,game_id=None):
    # Query the data store and get the approriate playerid
    # Set that queried data store object and set the appropriate action
    # Based on that action do the appropriate thing
    # Play
    # Draw
    # Fold 
    template = jinja_environment.get_template('action.html')
    game = Game.get_by_id(int(game_id))
    action = self.request.get('Action')
    user = users.get_current_user()
    bet = int(self.request.get('bet_field'))
    for player in game.players:
      if player.player_id == user.user_id():
        result = player

    if action == 'Play':
      value = GameUpdater(game).play(result,bet)
    elif action == 'Draw':
      value = GameUpdater(game).draw(result)
      if value == 'Cards' :
        self.redirect_to('table',game_id=game_id)
        return
    elif action == 'Fold':
        self.redirect_to('clear',game_id=game_id)
        return

    values = {
      'player' : result,
      'game' : game,
      'value' : value 
    }

    self.response.out.write(
        template.render(values)
    )

class PlayerHandler(webapp2.RequestHandler):
  def get(self,game_id=None):
    user = users.get_current_user()

    template = jinja_environment.get_template('player.html')

    game = Game.get_by_id(int(game_id))
    values = {
        'game' : game
    }

    for player in game.players:
      if player.player_id == user.user_id():
        self.redirect_to('table',game_id=game_id)

    self.response.out.write(
        template.render(values)
    )


  def post(self,game_id=None):
    user = users.get_current_user()
    game = Game.get_by_id(int(game_id))
    ## need to make a check to see if game exceeds max players
    game.players_current = game.players_current + 1
    player = Player(
            game_id = int(game_id),
            player_id = user.user_id(),
            name = self.request.get('player_name'),
            tokens = 1000,
            cards_not_visible = game.deck,
            )
    if not game.current_turn:
      game.current_turn = user.user_id()
      player.cards_visible = GameUpdater(game).deal_cards()

    player.put()
    game.players.append(player)

    game.put()
    self.redirect_to('table',game_id=game_id)


class TableHandler(webapp2.RequestHandler):
  def get(self,game_id=None):
    user = users.get_current_user()
    template = jinja_environment.get_template('game.html')
    if not game_id:
      self.response.write("You need to have a game_id")
      return

    try:
      game = Game.get_by_id(int(game_id))
      if not game:
        raise Exception("No table retrieved")

    except Exception as e:
      self.response.write("invalid table_id specified")
      return 

   # player = Player.query(ndb.AND(Player.game_id == int(game_id),Player.player_id == user.user_id()))
#    player = ndb.gql('SELECT * From Player')

    for player in game.players:
      if player.player_id == user.user_id():
        result = player


    values = {
      'game' : game,
      'curr_player' : result,
      'user_id' : user.user_id(),
    }

    self.response.out.write(
      template.render(values)
    )

class ClearHandler(webapp2.RequestHandler):
  def get(self,game_id=None):
    game = Game.get_by_id(int(game_id))
    user = users.get_current_user()
    player_array = []
    for player in game.players:
      if player.player_id == user.user_id():
        result = player
      else:
        player_array.append(player.player_id)
    if len(player_array) == 0:
      player_array.append(user.user_id())


    game.current_turn = random.choice(player_array)
    result.cards_visible = GameUpdater(game).deal_cards()
    game.common_cards_visible = []    
    GameUpdater(game).init_deck()
    result.put()
    game.put()
    self.redirect_to('table',game_id=game_id)

class StatusHandler(webapp2.RequestHandler):
  def get(self,game_id=None):
    return



url_routes = []
url_routes.append(
    routes.RedirectRoute(r'/',
                         handler=MainHandler,
                         strict_slash=True,
                         name="main")
)
url_routes.append(
    routes.RedirectRoute(r'/game',
                         handler=GameHandler,
                         strict_slash=True,
                         name="game")
)
url_routes.append(
    routes.RedirectRoute(r'/game/<game_id:\d+>/clear',
                         handler=ClearHandler,
                         strict_slash=True,
                         name="clear")
)
url_routes.append(
    routes.RedirectRoute(r'/game/<game_id:\d+>/status',
                         handler=StatusHandler,
                         strict_slash=True,
                         name="status")
)
url_routes.append(
    routes.RedirectRoute(r'/game/<game_id:\d+>/playerConnect',
                         handler=PlayerHandler,
                         strict_slash=True,
                         name="player")
)
url_routes.append(
    routes.RedirectRoute(r'/game/<game_id:\d+>/visible_table',
                         handler=TableHandler,
                         strict_slash=True,
                         name="table")
)
url_routes.append(
    routes.RedirectRoute(r'/game/<game_id:\d+>/action',
                         handler=ActionHandler,
                         strict_slash=True,
                         name="action")
)

base_app = webapp2.WSGIApplication(url_routes)

app = CorsApplication(base_app,
                      CorsOptions(allow_origins=True,
                                  continue_on_error=True))

