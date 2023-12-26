import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
import json
import asyncio
import random

class GraphNodeAgent(Agent):
    def get_noisy_value(self):
        noise = random.uniform(-1, 1) # Noise
        return self.value + noise

    class CommunicateNeighboursBehaviour(CyclicBehaviour):
        async def run(self):
            processing_delay = random.uniform(0, 1.0) # Random message processing delay
            await asyncio.sleep(processing_delay)

            if self.agent.active:
                msg = await self.receive(timeout=10)
                if msg:
                    content = json.loads(msg.body)
                    sender = str(msg.sender)
                    self.agent.received_values[sender] = content['value']

                    await asyncio.sleep(2) # Changed mean calculation condition to account for dynamic links
                    await self.agent.calculate_mean()

    class SendValueToNeighboursBehaviour(CyclicBehaviour):
        async def run(self):
            await asyncio.sleep(1 + random.uniform(0, 1.0)) # Random message sending delay
            if self.agent.active:
                for neighbor in self.agent.neighbors:
                    if random.random() < 0.8: # Chance to send message (dynamic links between agents)
                        message = Message(to=neighbor)
                        message.set_metadata("performative", "inform")
                        noisy_value = self.agent.get_noisy_value()
                        message.body = json.dumps({'value': noisy_value})
                        await self.send(message)
            else:
                self.kill()

    async def setup(self):
        self.received_values = {}
        self.active = True
        self.communicate_behaviour = self.CommunicateNeighboursBehaviour()
        self.send_behaviour = self.SendValueToNeighboursBehaviour()
        self.add_behaviour(self.communicate_behaviour)

    async def calculate_mean(self):
        old_mean = self.value
        total = sum(self.received_values.values()) + self.value
        self.value = total / (len(self.received_values) + 1)
        print(f'Agent {self.jid} calculated mean: {self.value}')

        if old_mean is not None and abs(self.value - old_mean) < 0.0001:
            print(f'Agent {self.jid} synchronized.')
            self.active = False
        else:
            self.active = True

async def main():
    agents = []

    node_values = [12, 25, 41]
    neighbors = [['agent_1@localhost'], 
                 ['agent_0@localhost', 'agent_2@localhost'], 
                 ['agent_1@localhost']]

    for i, (value, neighbor) in enumerate(zip(node_values, neighbors)):
        agent_jid = f'agent_{i}@localhost'
        agent_password = "123"
        agent = GraphNodeAgent(agent_jid, agent_password)
        agent.value = value
        agent.neighbors = neighbor
        agents.append(agent)

    for agent in agents:
        await agent.start()

    await asyncio.sleep(2)

    for agent in agents:
        agent.add_behaviour(agent.send_behaviour)

    await asyncio.sleep(100)

    for agent in agents:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())