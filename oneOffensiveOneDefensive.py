# baselineTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint

BELIEFS = [] #a list of counters corresponding to probability distributions over each agent
INITIALIZED = False


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
 
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)
    global INITIALIZED
    if INITIALIZED == True:
        return #only initialize global stuff once
    for i in range(gameState.getNumAgents()):
        BELIEFS.append(util.Counter())
    
    opponents = self.getOpponents(gameState)
    for opponent in opponents:
        initialPosition = gameState.getInitialAgentPosition(opponent)
        #print "initialPosition for agent " + str(opponent) + " is " + str(initialPosition)
        BELIEFS[opponent][initialPosition] = 1 #the rest are initialized to zero automatically

    INITIALIZED = True

  def observe(self, gameState):
    """
    updates the belief distribution over both enemies
    """
      
    enemies = self.getOpponents(gameState)
    agent_distances = gameState.getAgentDistances() #these are the observations
    for enemy in enemies:
        #first we will check if we have exact information
        position_reading = gameState.getAgentPosition(enemy)

        if position_reading != None:
            #print "successful position reading"
            #print "reading! : " + str(position_reading)
            new_belief_distribution = util.Counter()
            new_belief_distribution[position_reading] = 1.0
            BELIEFS[enemy] = new_belief_distribution
            continue
    
        #we don't know where the enemy is at this point, so we use exact inference
        noisy_distance = agent_distances[enemy]

        #print "noisy distance: " + str(noisy_distance)

        # the position of the calling agent
        my_position = gameState.getAgentPosition(self.index)
        # a new counter to store updated beliefs
        beliefs = util.Counter()

        for position in self.getLegalPositions(gameState):
            distance = util.manhattanDistance(position, my_position)
            beliefs[position] = BELIEFS[enemy][position] * gameState.getDistanceProb(distance, noisy_distance)
                #if BELIEFS[enemy][position] >= 0.05:
                #print distance
                #print "beliefs[position]: " + str(beliefs[position])

        beliefs.normalize()
        BELIEFS[enemy] = beliefs
        if BELIEFS[enemy].totalCount() == 0:
            self.initializeUniformly(enemy, gameState)

  def elapseTime(self, gameState):
    """
    elapses time for the enemy who went previously
    """
    #if I am first to play, I don't want to elapse time for the enemy who "went" before me - we're not gonna worry, we'll just elapse time anyway
    
    enemy_we_are_updating = (self.index + 3) % 4
    
    newBeliefs = util.Counter()
    for position in self.getLegalPositions(gameState):
        former_probability_of_position = BELIEFS[enemy_we_are_updating][position]
        actions = self.getPossibleActions(position, gameState)
        for action in actions:
            successor = self.getSuccessorPosition(position, action)
            newBeliefs[successor] += former_probability_of_position * (1.0 / len(actions))

    BELIEFS[enemy_we_are_updating] = newBeliefs

  def getLegalPositions(self, gameState):
    legalPositions = []
    width = gameState.data.layout.width
    height = gameState.data.layout.height
    for x in range(width):
        for y in range(height):
            if not gameState.hasWall(x,y):
                legalPositions.append((x,y))

    return legalPositions

  def getSuccessorPosition(self, initialPosition, action):
    """
    there's gotta be something that does this already
    """
    if action == 'North':
        return (initialPosition[0], initialPosition[1] + 1)
    if action == 'South':
        return (initialPosition[0], initialPosition[1] - 1)
    if action == 'East':
        return (initialPosition[0] + 1, initialPosition[1])
    if action == 'West':
        return (initialPosition[0] - 1, initialPosition[1])
    if action == 'Stop':
        return initialPosition

  def getPossibleActions(self, position, gameState):
    actions_to_return = []
    x,y = position
    if not gameState.hasWall(x+1, y):
        actions_to_return.append('East')
    if not gameState.hasWall(x-1, y):
        actions_to_return.append('West')
    if not gameState.hasWall(x, y+1):
        actions_to_return.append('North')
    if not gameState.hasWall(x, y-1):
        actions_to_return.append('South')
    actions_to_return.append('Stop')

    return actions_to_return

  def printBeliefs(self, enemy_index, gameState):
    print "beliefs for enemy " + str(enemy_index) + ":"
    legalPositions = self.getLegalPositions(gameState)
    for position in legalPositions:
        if BELIEFS[enemy_index][position] >= 0.1:
            print "(" + str(position[0]) + "," + str(position[1]) + "): " + str(BELIEFS[enemy_index][position])

  def getMostLikelyPosition(self, opponent):
    max_prob = 0.0
    most_likely_position = (0,0)
    for position in BELIEFS[opponent]:
        if BELIEFS[opponent][position] > max_prob:
            max_prob = BELIEFS[opponent][position]
            most_likely_position = position

    return most_likely_position

  def captureUpdate(self, gameState):
    myTeam = self.getTeam(gameState)
    for agentIndex in myTeam:
        enemies = self.getOpponents(gameState)
        for enemy in enemies:
            if gameState.getAgentPosition(agentIndex) == self.getMostLikelyPosition(enemy):
                #print "here"
                beliefs = util.Counter()
                for p in self.getLegalPositions(gameState):
                    beliefs[p] = 0
                    beliefs[gameState.getInitialAgentPosition(enemy)] = 1.0
                BELIEFS[enemy] = beliefs

  def initializeUniformly(self, opponent, gameState):
    legalPositions = self.getLegalPositions(gameState)
    probability_of_position = 1.0 / len(legalPositions)
    for position in legalPositions:
        BELIEFS[opponent][position] = probability_of_position

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    #print ""
    #print "entering chooseAction: currentAgent = " + str(self.index)
    opponents = self.getOpponents(gameState)
    #first update the distributions
    self.captureUpdate(gameState)
    self.elapseTime(gameState)
    
    """
    print "about to observe"
    for opponent in opponents:
        self.printBeliefs(opponent, gameState)
    self.observe(gameState)
    for opponent in opponents:
        self.printBeliefs(opponent, gameState)
    """
    self.observe(gameState)
    
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class OffensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()    
    features['successorScore'] = -len(foodList)#self.getScore(successor)
    
    myPos = successor.getAgentState(self.index).getPosition()

    features['pointsScore'] = self.getScore(successor)

    # if the pacman has some food and is near home, 'homeSickNess' goes up
    
    numCarrying = successor.getAgentState(self.index).numCarrying
    pos2 = successor.getAgentPosition(self.index)
    distanceHome = self.getMazeDistance(self.start,pos2)
    if numCarrying >= 1 and distanceHome <= 50:
        features['homesickness'] = 1.0 / distanceHome
    

    # Compute distance to nearest ghost if ghost is 3 or closer

    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]
    if len(ghosts) > 0:
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in ghosts]
        if min(dists) <= 3:
            features['ghostNear'] = 1.0 / min(dists)

    # Compute distance to the nearest food

    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
    return features

  def getWeights(self, gameState, action):
      return {'successorScore': 100, 'distanceToFood': -1, 'ghostNear': 100, 'homesickness': +2000, 'pointsScore': 10000}

class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    closest_ghost = None
    min_d = float("inf")

    opponents = self.getOpponents(gameState)

    # an array of two positions: each denoting an enemy's 
    # most likely coordinates. -1 for non-enemy. 

    most_likely_locations = [-1,-1,-1,-1]

    for enemy_index in opponents:
        most_likely_locations[enemy_index] = (0,0)

    for enemy_index in opponents:
        max_arg = ((0,0), 0.0)
        for x in BELIEFS[enemy_index]:
            p = BELIEFS[enemy_index][x] 
            if p >= max_arg[1]:
                max_arg = (x,p)
        most_likely_locations[enemy_index] = max_arg[0]
        #print most_likely_locations[enemy_index]
        #self.printBeliefs(enemy_index, gameState)

    distances = [self.getMazeDistance(myPos, position) for position in most_likely_locations if not position == -1 ]

    #print min(distances)
    features['distanceToNearestEnemy'] = min(distances)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'distanceToNearestEnemy': -10, 'stop': -100, 'reverse': -2}
