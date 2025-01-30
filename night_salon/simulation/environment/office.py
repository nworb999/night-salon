import random
from datetime import time
from typing import Dict, List, Optional
from night_salon.utils.types import Location, Agent, Action


class OfficeEnvironment:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.location_capacity = {
            Location.CONFERENCE_ROOM: 10,
            Location.WATER_COOLER: 3,
            Location.SMOKING_AREA: 4,
            Location.CUBICLES: 20,
            Location.BATHROOM: 2,
        }
        self.office_hours = {"start": time(9, 0), "end": time(17, 0)}  # 9 AM  # 5 PM
        self.possible_actions = {
            Location.CONFERENCE_ROOM: [Action.MEETING, Action.PRESENT, Action.LISTEN],
            Location.WATER_COOLER: [Action.CHAT, Action.DRINK],
            Location.SMOKING_AREA: [Action.SMOKE, Action.CHAT],
            Location.CUBICLES: [Action.WORK, Action.CHAT, Action.PHONE_CALL],
            Location.BATHROOM: [Action.USE_BATHROOM],
        }

        self.possible_thoughts = {
            Action.WORK: [
                "Need to finish this report",
                "Making good progress",
                "This code needs debugging",
                "Almost done with this task",
            ],
            Action.CHAT: [
                "Nice conversation",
                "Interesting office gossip",
                "Good to catch up",
            ],
        }

    def add_agent(self, agent_id: str, location: Location) -> bool:
        """Add a new agent to the environment"""
        if self._check_location_capacity(location):
            self.agents[agent_id] = Agent(
                id=agent_id,
                location=location,
                current_action=Action.WALK,
                objective="Starting work day",
                thought="Let's get started",
            )
            return True
        return False

    async def update_environment(self):
        """Update the environment state for each tick"""
        current_time = datetime.now().time()

        for agent_id, agent in self.agents.items():
            try:
                # Random chance to update agent's state
                if random.random() < 0.3:  # 30% chance each tick
                    await self._update_agent_state(agent)

                # Log the agent's current state
                self._print_agent_state(agent)

            except Exception as e:
                logger.error(f"Error updating agent {agent_id}: {str(e)}")

    async def _update_agent_state(self, agent: Agent):
        """Update an individual agent's state with realistic behavior"""
        # Decide if agent should change location
        if random.random() < 0.2:  # 20% chance to change location
            new_location = self._choose_new_location(agent.location)
            if new_location and self._check_location_capacity(new_location):
                agent.location = new_location

        # Update action based on location
        possible_actions = self.possible_actions[agent.location]
        agent.current_action = random.choice(possible_actions)

        # Update thought based on action
        if agent.current_action in self.possible_thoughts:
            agent.thought = random.choice(self.possible_thoughts[agent.current_action])

        # Update objective based on action and location
        agent.objective = self._generate_objective(agent.location, agent.current_action)

    def update_agent(
        self,
        agent_id: str,
        location: Optional[Location] = None,
        action: Optional[Action] = None,
        objective: Optional[str] = None,
        thought: Optional[str] = None,
    ) -> bool:
        """Update agent's state"""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]

        if location and self._check_location_capacity(location):
            agent.location = location
        if action:
            agent.current_action = action
        if objective:
            agent.objective = objective
        if thought:
            agent.thought = thought

        self._print_agent_state(agent)
        return True

    def _choose_new_location(self, current_location: Location) -> Optional[Location]:
        """Choose a new location for the agent to move to"""
        available_locations = [
            loc
            for loc in Location
            if loc != current_location and self._check_location_capacity(loc)
        ]
        return random.choice(available_locations) if available_locations else None

    def _generate_objective(self, location: Location, action: Action) -> str:
        """Generate a contextual objective based on location and action"""
        if location == Location.CONFERENCE_ROOM:
            return (
                "Participating in daily standup"
                if action == Action.MEETING
                else "Attending presentation"
            )
        elif location == Location.CUBICLES:
            return (
                "Working on assigned tasks"
                if action == Action.WORK
                else "Taking a short break"
            )
        elif location == Location.WATER_COOLER:
            return "Taking a refreshment break"
        elif location == Location.SMOKING_AREA:
            return "Taking a smoke break"
        elif location == Location.BATHROOM:
            return "Taking a bathroom break"
        return "Going about their day"

    def _check_location_capacity(self, location: Location) -> bool:
        """Check if location has available capacity"""
        current_count = sum(
            1 for agent in self.agents.values() if agent.location == location
        )
        return current_count < self.location_capacity[location]

    def _print_agent_state(self, agent: Agent):
        """Print the current state of an agent"""
        print(f"\nAgent {agent.id}:")
        print(f"Location: {agent.location.name}")
        print(f"Action: {agent.current_action.name}")
        print(f"Objective: {agent.objective}")
        print(f"Thought: {agent.thought}")
