import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
import json
import asyncio
import random

class GraphNodeAgent(Agent):
    def __init__(self, jid, password, alpha, b_values, initial_value):
        super().__init__(jid, password)
        self.alpha = alpha
        self.b_values = b_values
        self.value = initial_value

    class CommunicateNeighboursBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.active:
                msg = await self.receive(timeout=10)
                if msg:
                    processing_delay = random.uniform(0, 1.0) # Random message processing delay
                    await asyncio.sleep(processing_delay)
                    
                    content = json.loads(msg.body)
                    sender = str(msg.sender)
                    self.agent.received_values[sender] = content['value']

                    if len(self.agent.received_values) == len(self.agent.neighbors):
                        await self.agent.calculate_control_action()

    class SendValueToNeighboursBehaviour(CyclicBehaviour):
        async def run(self):
            await asyncio.sleep(1)
            if self.agent.active:
                for neighbor in self.agent.neighbors:
                    if random.random() < 0.8: # Chance to send message (dynamic links between agents)
                        message = Message(to=neighbor)
                        message.set_metadata("performative", "inform")
                        message.body = json.dumps({'value': self.agent.value + random.uniform(-1, 1)}) # Apply noise
                        await self.send(message)

                self.agent.received_values.clear()
            else:
                self.kill()

    async def calculate_control_action(self):
        y_i_i_t = self.value + random.uniform(-1, 1)
        control_sum = 0

        for neighbor, value in self.received_values.items():
            y_i_j_t = value
            b_i_j = self.b_values.get(neighbor, 0)
            control_sum += b_i_j * (y_i_j_t - y_i_i_t)

        u_i_t = self.alpha * control_sum
        self.value += u_i_t

        print(f'Agent {self.jid} updated value: {self.value}')

    async def setup(self):
        self.received_values = {}
        self.active = True
        self.communicate_behaviour = self.CommunicateNeighboursBehaviour()
        self.send_behaviour = self.SendValueToNeighboursBehaviour()
        self.add_behaviour(self.communicate_behaviour)

async def main():
    agents = []

    node_values = [12, 25, 41]

    neighbors = [['agent_1@localhost'], 
                 ['agent_0@localhost', 'agent_2@localhost'], 
                 ['agent_1@localhost']]

    alpha_value = 0.5

    b_values = {'agent_0@localhost': 1, 'agent_1@localhost': 1, 'agent_2@localhost': 1}

    for i, (value, neighbor) in enumerate(zip(node_values, neighbors)):
        agent_jid = f'agent_{i}@localhost'
        agent_password = "123"
        agent = GraphNodeAgent(agent_jid, agent_password, alpha_value, b_values, value)
        agent.neighbors = neighbor
        agents.append(agent)

    for agent in agents:
        await agent.start()

    await asyncio.sleep(2)

    for agent in agents:
        agent.add_behaviour(agent.send_behaviour)

    await asyncio.sleep(10)

    for agent in agents:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())