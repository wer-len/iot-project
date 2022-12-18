from asyncua import Client
from asyncio import get_event_loop, sleep, gather
from agent import Agent
from config import Config

async def main():
  config = Config()
  agents = []

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

    while True:
      for agent in agents:
        await gather(*agent.get_tasks())
      await sleep(1)


if __name__ == '__main__':
  loop = get_event_loop()
  loop.run_until_complete(main())
