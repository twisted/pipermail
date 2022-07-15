# Should I be using text messages, or be using python lists?
# Snippet from tutorial: finger19a.py
	def getUser(self, user):
		return defer.succeed(self.users.get(user, "No such user"))
	def getUsers(self):
		return defer.succeed(self.users.keys())
	def setUser(self, user, status):
		self.users[user] = status

# Here's my psuedo code test, using pygame + twisted
import twisted stuff # psuedo code import

# == game_client.py ==
class GameClient( basic.LineReceiver ): # or wrong class for the client?
	def __init__(self):
		self.asteroids = [] # list of: Asteroid(Actor):
		self.bullets = [] # list of: Bullet(Actor):
		self.ships = [] # list of: Ship(Actor):
		self.state = "round start"

	def keyboard_input(self):
		if keyPressed['fire'] and cooldownDone():
			msg = "fire, bullet, %d, %d" % ( self.loc.x, self.loc.y )
			self.factory.server.message( msg )

	def loop(self):
		"""main loop"""
		# next level/round started, so spawn asteroids, etc
		if self.state == "round start":
			self.factory.server.message( "ready" )

		# in the middle of the round
		elif self.state == "round":
			self.keyboard_input()
			physics_update()
			graphics_draw()

			# update my location to server
			if time_elapsed( 150 ms ): # but only every Xms elapsed
				id, x, y = self.ship.ID, self.ship.loc.x, self.ship.loc.y
				self.factory.server.message("player, %d, %d, %d" % (id, x, y ) )

		# else: always:
		sleep() # or not?

	def lineReceived(self, line):
		"""string received command from clients
		example: 'fire, bullet, x, y' """
		cmds = splitIntoCmds(line)
		if cmds[0] == "fire":
			self.spawn( cmds[1:] ) # arg is the rest of the command
		if cmds[0] == "player":
			id, x, y = cmds[1], cmds[2], cmds[3]
			self.ships[id].loc = (x, y )
		if cmds[0] == "spawn":
			# server spawned something, and is notify-ing me of it
			self.spawn( cmds[1:] )

# == game_server.py ==
class GameServer(basic.LineReceiver): # Maybe wrong type to descend from
	def __init__(self):
		self.asteroids = [] # list of: Asteroid(Actor):
		self.bullets = [] # list of: Bullet(Actor):
		self.ships = [] # list of: Ship(Actor):
		self.state = "round start"

	def randomAsteroids(self):
		"""init randomized asteroids"""
		self.spawn( "asteroid, %d, %d" % ( rand(), rand() )

	def loop(self):
		"""main loop"""
		if self.state = "round start":
			self.randomAsteroids()
			# could wait till I get a 'ready' from all players (but I dont yet)
			self.state = "round" 
		elif self.state = "round":
			self.update() # update physics
			# also update players movements to each other ( every Xms? )
			for c in self.factory.clients:
				c.message( "player, ID, loc" )

		sleep() # or not ?

	def spawn(self, cmds):
		"""spawn something: unit, x, y and notify clilents.
		constructors are: Bullet(x,y) and Asteroid(x,y)"""
		unit, x, y = cmds[0], cmds[1], cmds[2]
		if unit == "bullet":
			self.bullets.append( Bullet( x, y ) )
		elif unit == "asteroid":
			self.asteroids.append( Asteroid( x, y ) )

		# notify clients of new Actor()'s
		msg = "spawn, %s, %d, %d" % ( unit, x, y )
		for c in self.factory.clients:
			c.message(msg)

	def lineReceived(self, line):
		"""string received command from clients
		example: 'fire, bullet, x, y' or 'player, ID, x, y' """
		cmds = splitIntoCmds(line)
		if cmds[0] == "fire":
			self.spawn( cmds[1:] ) # arg is the rest of the command
		if cmds[0] == "player":
			id, x, y = cmds[1], cmds[2], cmds[3]
			self.ships[id].loc = (x, y )
		if cmds[0] == "ready":
			self.ships[id].ready = True
		