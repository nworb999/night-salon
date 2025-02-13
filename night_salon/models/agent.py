# src/models/agent.py
class Agent:
    def __init__(self, agent_id):
        self.id = agent_id
        self.position = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.state = {
            "health": 100,
            "energy": 100,
            "current_action": None,
            "target": None
        }
    
    def update_position(self, x, y, z):
        self.position = (x, y, z)
    
    def update_rotation(self, x, y, z):
        self.rotation = (x, y, z)