import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """

    from math import floor
    def calcBlock(self,p,q):
        # block = int(((floor(i/sboard.p) * sboard.p) + floor(j/sboard.q)))
        return (p//3) + 3*(q//3)

    def updateModVars(self,mod_vars,p,q,value):

        # if variable is already assigned, do nothing
        if self.gameboard.board[p][q]:
            return

        cur_mod_var = mod_vars[p][q]

        # if variable not in mod_vars, add
        if not cur_mod_var:
            block = self.calcBlock(p,q)
            cur_mod_var = Variable.Variable(list(range(9)),p,q,block)
            mod_vars[p][q] = cur_mod_var

        # remove value from domain of variable

        cur_mod_var.removeValueFromDomain(value)

    def checkNeighborRow(self,mod_vars,p,q,value):
        for pSub in range(9):
            # don't check the same tile
            if pSub==p:
                pass
            self.updateModVars(mod_vars,pSub,q,value)

    def checkNeighborColumn(self,mod_vars,p,q,value):
        for qSub in range(9):
            # don't check the same tile
            if qSub==q:
                pass
            self.updateModVars(mod_vars,p,qSub,value)

    def checkNeighborBlock(self,mod_vars,p,q,value):
        block = self.calcBlock(p,q)
        
        for p_ in range(3):
            for q_ in range(3):
                pSub = p_ + 3*(block%3)
                qSub = q_ + 3*(block//3)

                if pSub==p and qSub==q:
                    pass
                self.updateModVars(mod_vars,pSub,qSub,value)

    def checkNeighbors(self,mod_vars,p,q):
        value = self.gameboard.board[p][q]

        self.checkNeighborRow(mod_vars,p,q,value)
        self.checkNeighborColumn(mod_vars,p,q,value)
        self.checkNeighborBlock(mod_vars,p,q,value)

    def forwardChecking ( self ):
        mod_vars = []               #list of modified items
        modified_vars_dict = {}     #dictionary that we created to learn which variables were modified
        assigned_list = []
        consistent = True

        #get all the constraints (network here is CSP) and put appropriate variables in a list
        for constraints in self.network.constraints:
            for var in constraints.vars:
                if var.isAssigned():                #check to see that a variable is already assigned (non 0)
                    assigned_list.append(var)       #it's assigned so added into list to take care of its neigbors below.
        
        for assigned_variables in assigned_list:   #here take care of the neigbors of the list
            for neighbor in self.network.getNeighborsOfVariable(assigned_variables):    #pruning
                if neighbor.isChangeable() and not neighbor.isAssigned():               #If it's changable and not yet assigned,
                    assignment = assigned_variables.getAssignment()                     # getAssignment returns the assigned value or 0 if unassigned
                    if neighbor.getDomain().contains(assignment):                       # if the neighbor's domain has contains that assignment                    
                        mod_vars.append((neighbor, assignment))                         # add that into list as a tuple with its assignment
        
        for tuple in mod_vars:                                                          # go over each tuple and push each variable we have into trail
            self.trail.push(tuple[0])
            tuple[0].removeValueFromDomain(tuple[1])                                    # after pushing that into trail, remove assignment from domain
            modified_vars_dict[tuple[0]] = tuple[0].getDomain()                         # add that into dictionary
            if tuple[0].size() == 0:                                                    # size return domain size, if (after removals) there is no more option left
                consistent = False                                                      #  then it's not consistent and make that appropriate variable flag False.
        return (modified_vars_dict,consistent)                      
        
        '''
                    var_list = self.network.getVariables()
                    for var in var_list:
                        if var.isChangeable():
                            domain = var.getDomain()  # get the domain from variable.py
                            trail = self.trail.placeTrailMarker()
                            for value in domain:
                                var.assignValue(value)
                                consistent = True
                                # check consistency with its neighbors
                                for neighbor in self.network.getNeighborsOfVariable(var):
                                    if neighbor.isChangeable() and not neighbor.hasValue(value):
                                        consistent = False
                                        break
                                if consistent:
                                    modified_vars[var] = var.getAssignment()
                                    self.updateModVars(mod_vars, p, q, var)
                                    break
                                else:
                                    var.unassignValue()
                            self.trail.push(var)
                            if not var.getDomain():
                                return (modified_vars, False)
        return (modified_vars, True)                            #all assignments are legit and consistent, so return the tuple
        '''

    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        return ({}, False)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        return None

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        return None

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        return None

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
