# src/models/events.py
class UnityEvent:
    def __init__(self, type, agent_id, **kwargs):
        self.type = type
        self.agent_id = agent_id
        self.data = kwargs

    def __str__(self):
        return f"UnityEvent(type={self.type}, agent_id={self.agent_id}, data={self.data})"
