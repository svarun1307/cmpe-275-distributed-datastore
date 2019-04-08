class State():
    def __init__(self,state):
        self.state=state
    def isLeader(self):
        return self.state
    def changeState(self,state):
        if(state!= self.state):
            self.state=state
            return True
        else:
            return False
        