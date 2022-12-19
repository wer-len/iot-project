from asyncua import Client
from asyncio import get_event_loop, sleep, gather
from agent import Agent
from config import Config

async def main():
  config = Config()
  agents = []
  subscriptions = []

  async with Client(config.opcua_address) as client:
    objects = await client.get_objects_node().get_children()
    for obj in objects:
      name = (await obj.read_browse_name()).Name
      if name != 'Server':
        device_connection_string = config.get_device_connection_string('devices', name)

        agent = Agent(
          device=obj,
          opcua_client=client,
          connection_string=device_connection_string
        )

        agents.append(agent)

        subcription = await client.create_subscription(200, agent)
        await subcription.subscribe_data_change(await agent.subscribed_nodes)
        subscriptions.append(subcription)

    while True:
      for agent in agents:
        await gather(*agent.get_tasks())
      await sleep(1)


if __name__ == '__main__':
  loop = get_event_loop()
  loop.run_until_complete(main())
