import random
from utils.types import Location, Action
from night_salon.agents.base import BaseAgent

class WorkerAgent(BaseAgent):
    def __init__(self, agent_id: str, simulation_url: str):
        super().__init__(agent_id, simulation_url)
        
        # Personality traits (0.0 to 1.0)
        self.sociability = random.uniform(0.3, 0.8)
        self.productivity = random.uniform(0.4, 0.9)
        self.stress_tolerance = random.uniform(0.3, 0.8)
        
        # Action weights for different needs
        self.action_effects = {
            Action.WORK: {"energy": -0.1, "stress": 0.15, "social": -0.05},
            Action.CHAT: {"energy": -0.05, "stress": -0.2, "social": 0.3},
            Action.DRINK: {"energy": 0.2, "stress": -0.1, "social": 0.1},
            Action.REST: {"energy": 0.3, "stress": -0.2, "social": 0.0},
        }

    async def update_cognitive_state(self):
        """Update cognitive state based on current activity and needs"""
        effects = self.action_effects.get(self.functional_state.current_action, {})
        
        # Update state based on current action
        self.cognitive_state.energy_level = max(0.0, min(1.0,
            self.cognitive_state.energy_level + effects.get("energy", 0)))
        self.cognitive_state.stress_level = max(0.0, min(1.0,
            self.cognitive_state.stress_level + effects.get("stress", 0)))
        self.cognitive_state.social_need = max(0.0, min(1.0,
            self.cognitive_state.social_need + effects.get("social", 0)))
            
        # Update emotion based on state
        self.cognitive_state.emotion = self._determine_emotion()
        
    def _determine_emotion(self) -> str:
        """Determine emotion based on current state"""
        if self.cognitive_state.stress_level > 0.8:
            return "stressed"
        if self.cognitive_state.energy_level < 0.2:
            return "tired"
        if self.cognitive_state.social_need > 0.8:
            return "lonely"
        if self.cognitive_state.stress_level < 0.3 and self.cognitive_state.energy_level > 0.7:
            return "happy"
        return "neutral"

    async def decide_next_action(self) -> dict:
        """Decide next action based on current needs and state"""
        await self.update_cognitive_state()
        
        # Determine primary need
        needs = {
            "energy": self.cognitive_state.energy_level < 0.3,
            "stress": self.cognitive_state.stress_level > 0.7,
            "social": self.cognitive_state.social_need > 0.7
        }
        
        # Choose appropriate action based on strongest need
        if needs["energy"]:
            new_action = Action.REST
            new_location = Location.CUBICLES
            animation = "sitting"
        elif needs["stress"]:
            new_action = random.choice([Action.DRINK, Action.SMOKE])
            new_location = (Location.WATER_COOLER if new_action == Action.DRINK 
                          else Location.SMOKING_AREA)
            animation = "standing"
        elif needs["social"]:
            new_action = Action.CHAT
            new_location = random.choice([Location.WATER_COOLER, Location.CUBICLES])
            animation = "talking"
        else:
            new_action = Action.WORK
            new_location = Location.CUBICLES
            animation = "typing"

        # Update states
        self.functional_state.location = new_location
        self.functional_state.current_action = new_action
        self.functional_state.current_animation = animation
        self.cognitive_state.objective = self._generate_objective(new_action)
        self.cognitive_state.thought = self._generate_thought(new_action)
        
        return self.get_state_update()

    def _generate_objective(self, action: Action) -> str:
        """Generate contextual objective based on action"""
        objectives = {
            Action.WORK: "Focusing on tasks",
            Action.CHAT: "Taking a social break",
            Action.DRINK: "Getting refreshed",
            Action.REST: "Recharging energy",
            Action.SMOKE: "Taking a smoke break"
        }
        return objectives.get(action, "Going about my day")

    def _generate_thought(self, action: Action) -> str:
        """Generate contextual thought based on action and emotion"""
        thoughts = {
            ("WORK", "stressed"): "Need to meet these deadlines",
            ("WORK", "neutral"): "Making steady progress",
            ("WORK", "happy"): "In the flow, feeling productive",
            ("CHAT", "lonely"): "Really need some social interaction",
            ("CHAT", "happy"): "Good to connect with colleagues",
            ("REST", "tired"): "Need to recharge",
        }
        return thoughts.get((action.name, self.cognitive_state.emotion), 
                          "Just another moment in the day")