class UnityEvent:
    def __init__(self, type, agent_id, **kwargs):
        self.type = type
        self.agent_id = agent_id
        # Instead of storing kwargs in data, store them directly in the event
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        attrs = {k: v for k, v in self.__dict__.items() 
                if k not in ['type', 'agent_id']}
        return f"UnityEvent(type={self.type}, agent_id={self.agent_id}, {attrs})"
