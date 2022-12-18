from azure.iot.device import IoTHubDeviceClient, Message, MethodRequest, MethodResponse
from asyncua.common.node import Node
from asyncua.ua import Variant, VariantType
from asyncua import Client
import json
from datetime import datetime
from typing import Literal

class Agent:
  def __init__(self, device: Node, opcua_client: Client, connection_string: str):
    self.device = device
    self.opcua_client = opcua_client
    self.connection_string = connection_string

    self.iot_client = IoTHubDeviceClient.create_from_connection_string(self.connection_string)
    self.iot_client.connect()

    self.iot_client.on_twin_desired_properties_patch_received = self.on_twin_desired_properties_patch_received
    self.iot_client.on_method_request_received = self.on_method_request_received

    self.tasks = []

  def get_tasks(self):
    tasks = [*self.tasks, self.send_telemetry()]
    self.tasks = []
    return tasks

  async def get_device_property(self, property_name: str, node: bool = False):
    if node:
      return await self.device.get_child(property_name)
    return await (await self.device.get_child(property_name)).read_value()

  async def set_device_property(self, property_name: str, value: Variant):
    await (await self.device.get_child(property_name)).write_value(value)

  async def call_device_method(self, method_name: str):
    return await self.device.call_method(method_name)

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

  def on_twin_desired_properties_patch_received(self, patch: dict):
    if 'ProductionRate' in patch:
      print('Zmieniono wartość ProductionRate na ' + str(patch['ProductionRate']))
      self.tasks.append(
        self.set_device_property('ProductionRate', Variant(patch['ProductionRate'], VariantType.Int32))
      )

  def on_method_request_received(self, method_request: MethodRequest):
    method_name = method_request.name
    if method_name in ['EmergencyStop', 'ResetErrorStatus']:
      self.tasks.append(self.call_device_method(method_name))
      response = MethodResponse.create_from_method_request(method_request, 200, 'OK')
    elif method_name == 'MaintenanceDone':
      self.iot_client.patch_twin_reported_properties({'MaintenanceDone': datetime.now().isoformat()})
      response = MethodResponse.create_from_method_request(method_request, 200, 'OK')
    else:
      print('Nieznana metoda: ' + method_name)
      response = MethodResponse.create_from_method_request(method_request, 404, 'Nieznana metoda')
    self.iot_client.send_method_response(response)
    
    
  