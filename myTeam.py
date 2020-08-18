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
FINDFOOD = 0
RETURNHOME = 1
DEFENDFOOD1 = 2 #chase after my enemy (he's on my side)
DEFENDFOOD2 = 3 #defend a specific border spot closely
DEFENDFOOD3 = 4 #defend a specific border spot looselys
FINDCAPSULE = 5
SCAREDTIME = 0 #this is a variable

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'ReflexCaptureAgent', second = 'ReflexCaptureAgent'):
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

  def getMyEnemy(self):
    return (self.index + 3) % 4

  def initializeUniformly(self, opponent, gameState):
    legalPositions = self.getLegalPositions(gameState)
    probability_of_position = 1.0 / len(legalPositions)
    for position in legalPositions:
        BELIEFS[opponent][position] = probability_of_position

  def isOnMySide(self, position, gameState):
    width = gameState.data.layout.width
    leftSide = None
    if position[0] <= width / 2 - 1:
        leftSide = True
    else:
        leftSide = False
    if self.red:
        return leftSide
    else:
        return not leftSide


  def getBorderLocations(self, gameState):
    """
    returns a tuple of positions, with the home side listed first
    """
    borderLocations = []
    width = gameState.data.layout.width
    height = gameState.data.layout.height
    if self.red:
        x = width / 2 - 1
        for y in range(height):
            if not gameState.hasWall(x,y) and not gameState.hasWall(x+1, y):
                borderLocations.append(((x,y),(x+1,y)))
    else:
        x = width / 2
        for y in range(height):
            if not gameState.hasWall(x,y) and not gameState.hasWall(x-1, y):
                borderLocations.append(((x,y),(x-1,y)))

    return borderLocations

  def minDistanceToHomeBorder(self, position, gameState):
    borderPositions = self.getBorderLocations(gameState)
    minDist = float('inf')
    for borderPosition in borderPositions:
        dist = self.getMazeDistance(borderPosition[0], position)
        if dist < minDist:
            minDist = dist
    return minDist

  def getLegalPositionsOnSide(self, homeSide, gameState):
    legalPositions = []
      
    width = gameState.data.layout.width
    height = gameState.data.layout.height
    left = None
    right = None
    if (homeSide and self.red) or ((not homeSide) and (not self.red)):
        left = 0
        right = width / 2 - 1
    else:
        left = width / 2
        right = width - 1
    for x in range(left, right + 1):
        for y in range(0, height):
            if gameState.hasWall(x,y):
                continue
            else:
                legalPositions.append((x,y))

    return legalPositions


  def getMazeDistanceGivenPositionSubset (self, start, final, legal):
    #print "start: " + str(start)
    #print "final: " + str(final)
    
    visited_positions = []
    frontier = util.Queue()
    frontier.push((start, None))
    
    while True:
        if frontier.isEmpty():
            return -1
    
        node = frontier.pop()
        if node[0] == final:
            distance = 0
            currentNode = node
            while not currentNode[1] == None:
                distance +=1
                currentNode = currentNode[1]
            #print distance
            return distance

        if not node[0] in visited_positions:
            visited_positions.append(node[0])
            successors = self.getSuccessors(legal, node[0])
            for s in successors:
                if not s in visited_positions:
                    frontier.push((s, node))
    print "fail"
    return -1


  def getSuccessors(self, legal, position):
    """
    helper method for getMazeDistanceGivenPositionSubset
    """
    successors = []
    x,y = position
    
    if (x+1, y) in legal:
        successors.append((x+1, y))
    if (x-1, y) in legal:
        successors.append((x-1, y))
    if (x, y+1) in legal:
        successors.append((x, y+1))
    if (x, y-1) in legal:
        successors.append((x, y-1))
    
    return successors


  def chooseAction(self, gameState):
    actions = gameState.getLegalActions(self.index)
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
    """
    Picks among the actions with the highest Q(s,a).
    """
    #first update the distributions
    self.captureUpdate(gameState)
    self.elapseTime(gameState)
    
    self.observe(gameState)
    mode = self.getMode(gameState)
    #print mode
    """
    if self.index == self.getTeam(gameState)[1]:
        if mode == 0:
            print "find food"
        elif mode == 1:
            print "return with food"
        else:
            print "defending"
    """
    
    # profile evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a, mode) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    toReturn = random.choice(bestActions)
    
    #updating scared timer
    global SCAREDTIME
    
    successor = self.getSuccessor(gameState, toReturn)
    myTeam = self.getTeam(gameState)
    capsules = self.getCapsules(gameState)
    for agent in myTeam:
        position = successor.getAgentState(agent).getPosition()
        for capsule in capsules:
            if position == capsule:
                SCAREDTIME = 40

    if SCAREDTIME > 0:
        lowerIndexOnMyTeam = min(myTeam[0], myTeam[1])
        if self.index == lowerIndexOnMyTeam:
            SCAREDTIME -=1

    return toReturn

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

  def evaluate(self, gameState, action, mode):
    successor = self.getSuccessor(gameState, action)
    
    newState = successor.getAgentState(self.index)
    oldState = gameState.getAgentState(self.index)
    myPos = successor.getAgentState(self.index).getPosition()
    
    if mode == FINDCAPSULE:
        capsules = self.getCapsules(gameState)
        minDistanceToCapsule = float('inf')
        nearestCapsule = None
        for capsule in capsules:
            distanceToCapsule = self.getMazeDistance(myPos, capsule)
            if distanceToCapsule < minDistanceToCapsule:
                minDistanceToCapsule = distanceToCapsule
                nearestCapsule = capsule
        if minDistanceToCapsule == 0:
            return 100
        else:
            return 1.0 / minDistanceToCapsule
    
    if mode == FINDFOOD:
        foodList = self.getFood(successor).asList()
        minDistanceToFood = float('inf')
        if len(foodList) > 0: # This should always be True,  but better safe than sorry
            minDistanceToFood = min([self.getMazeDistance(myPos, food) for food in foodList])
        if newState.numCarrying > oldState.numCarrying:
            return 100
        else:
            return 1.0 / minDistanceToFood

    if mode == RETURNHOME:
        minDistanceToHomeBorder = self.minDistanceToHomeBorder(myPos, gameState)
        if minDistanceToHomeBorder == 0:
            return 100
        else:
            return 1.0 / minDistanceToHomeBorder

    #at this point we are doing some kind of defending
    myEnemy = self.getMyEnemy()
    mostLikelyLocationOfMyEnemy = self.getMostLikelyPosition(myEnemy)
    if mode == DEFENDFOOD1:
        valueToMinimize = self.getMazeDistanceGivenPositionSubset(mostLikelyLocationOfMyEnemy, myPos, self.getLegalPositionsOnSide(True,gameState))
        if valueToMinimize == 0:
            return 100
        else:
            return 1.0 / valueToMinimize

    #at this point we're defending the border in some way
    borderPositions = self.getBorderLocations(gameState)
    nearestBorderToEnemy = None
    lowestDistance = float('inf')
    for borderPosition in borderPositions:
        enemyDist = self.getMazeDistanceGivenPositionSubset(mostLikelyLocationOfMyEnemy, borderPosition[1], self.getLegalPositionsOnSide(False,gameState))
        if enemyDist < lowestDistance:
            lowestDistance = enemyDist
            nearestBorderToEnemy = borderPosition

    if mode == DEFENDFOOD2:
        myDistToNearestBorderToEnemy = self.getMazeDistanceGivenPositionSubset(myPos , nearestBorderToEnemy[0], self.getLegalPositionsOnSide(True,gameState))
        if myDistToNearestBorderToEnemy == 0:
            return 100
        else:
            return 1.0 / myDistToNearestBorderToEnemy
            
    #at this point we are certainly in DEFENDFOOD3
    width = gameState.data.layout.width
    y = mostLikelyLocationOfMyEnemy[1]
    left = None
    right = None
    if self.red:
        left = 0
        right = width / 2 - 1
    else:
        left = width / 2
        right = width - 1

    bestPosition = None
    minDistToClosestBorder = float('inf')
    for x in range(left, right + 1):
        if gameState.hasWall(x,y):
            continue
        dist = self.getMazeDistanceGivenPositionSubset((x,y), nearestBorderToEnemy[0], self.getLegalPositionsOnSide(True, gameState))
        if dist < minDistToClosestBorder:
            minDistToClosestBorder = dist
            bestPosition = (x,y)
    valueToMinimize = self.getMazeDistanceGivenPositionSubset(myPos, bestPosition, self.getLegalPositionsOnSide(True, gameState))
    if valueToMinimize == 0:
        return 100
    else:
        return 1.0 / valueToMinimize




  def getMode(self, gameState):

    if SCAREDTIME > 20:
        return FINDFOOD

    myPos = gameState.getAgentPosition(self.index)
    myState = gameState.getAgentState(self.index)
    
    foodList = self.getFood(gameState).asList()
    minDistanceToFood = float('inf')
    nearestFood = None
    if len(foodList) > 0: # This should always be True,  but better safe than sorry
        for food in foodList:
            distanceToFood = self.getMazeDistance(myPos, food)
            if distanceToFood < minDistanceToFood:
                minDistanceToFood = distanceToFood
                nearestFood = food

    opponents = self.getOpponents(gameState)
    minDistanceToOpponent = float('inf')
    nearestOpponentLocation = None
    for opponent in opponents:
        distance = self.getMazeDistance(myPos, self.getMostLikelyPosition(opponent))
        #if self.isScared(opponent, gameState):
            #continue
        if distance < minDistanceToOpponent:
            minDistanceToOpponent = distance

    capsules = self.getCapsules(gameState)
    minDistanceToCapsule = float('inf')
    nearestCapsule = None
    for capsule in capsules:
        distanceToCapsule = self.getMazeDistance(myPos, capsule)
        if distanceToCapsule < minDistanceToCapsule:
            minDistanceToCapsule = distanceToCapsule
            nearestCapsule = capsule

    myEnemy = self.getMyEnemy()
    mostLikelyLocationOfMyEnemy = self.getMostLikelyPosition(myEnemy)

    distFromOpponentToNearestFood = self.getMazeDistance(mostLikelyLocationOfMyEnemy, nearestFood)
    if nearestCapsule == None:
        distFromOpponentToNearestCapsule = float('inf')
    else:
        distFromOpponentToNearestCapsule = self.getMazeDistance(mostLikelyLocationOfMyEnemy, nearestCapsule)

    if not self.isOnMySide(myPos, gameState):

        if minDistanceToCapsule < min(minDistanceToOpponent, distFromOpponentToNearestCapsule):
            return FINDCAPSULE
        elif minDistanceToFood + self.minDistanceToHomeBorder(nearestFood, gameState) < min(minDistanceToOpponent, distFromOpponentToNearestFood):
            return FINDFOOD
        else:
            return RETURNHOME
  
    #at this point I am on my home side
    if self.isOnMySide(mostLikelyLocationOfMyEnemy, gameState):
        if mostLikelyLocationOfMyEnemy[0] < myPos[0] - 3:
            return FINDFOOD
        else:
            return DEFENDFOOD1
            
    #at this point I am on my side, and he is on his
    if self.minDistanceToHomeBorder(self.getMostLikelyPosition(myEnemy), gameState) > 2 * self.minDistanceToHomeBorder(myPos, gameState):
        if minDistanceToCapsule < min(minDistanceToOpponent, distFromOpponentToNearestCapsule):
            return FINDCAPSULE
        elif minDistanceToFood + self.minDistanceToHomeBorder(nearestFood, gameState) < min(minDistanceToOpponent, distFromOpponentToNearestFood):
            return FINDFOOD
    
    #at this point we are defending the border in some way
    
    borderPositions = self.getBorderLocations(gameState)
    nearestBorderToEnemy = None
    lowestDistance = float('inf')
    for borderPosition in borderPositions:
        enemyDist = self.getMazeDistanceGivenPositionSubset(mostLikelyLocationOfMyEnemy, borderPosition[1], self.getLegalPositionsOnSide(False,gameState))
        if enemyDist < lowestDistance:
            lowestDistance = enemyDist
            nearestBorderToEnemy = borderPosition

    myDistToNearestBorderToEnemy = self.getMazeDistanceGivenPositionSubset(myPos , nearestBorderToEnemy[0], self.getLegalPositionsOnSide(True,gameState))

    if myDistToNearestBorderToEnemy < lowestDistance - 1:
        return DEFENDFOOD3
    else:
        return DEFENDFOOD2















