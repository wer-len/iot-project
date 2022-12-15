from azure.iot.device import IoTHubDeviceClient, Message
from asyncua.common.node import Node
from asyncua import Client
import json
from typing import Literal

class Agent:
  def __init__(self, device: Node, opcua_client: Client, connection_string: str):
    self.device = device
    self.opcua_client = opcua_client
    self.connection_string = connection_string

    self.iot_client = IoTHubDeviceClient.create_from_connection_string(self.connection_string)
    self.iot_client.connect()

  async def get_device_property(self, property_name: str, node: bool = False):
    if node:
      return await self.device.get_child(property_name)
    return await (await self.device.get_child(property_name)).read_value()

  def send_message(self, data: dict, message_type: Literal['telemetry', 'event']):
    data['message_type'] = message_type
    message = Message(
        data=json.dumps(data),
        content_encoding='utf-8',
        content_type='application/json'
    )

    self.iot_client.send_message(message)

  async def send_telemetry(self):
    data = {
        "WorkorderId": await self.get_device_property('WorkorderId'),
        "ProductionStatus": await self.get_device_property('ProductionStatus'),
        "GoodCount": await self.get_device_property('GoodCount'),
        "BadCount": await self.get_device_property('BadCount'),
        "Temperature": await self.get_device_property('Temperature')
    }

    print(data)
    self.send_message(data, 'telemetry')

  