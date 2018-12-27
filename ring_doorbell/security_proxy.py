# coding: utf-8
# vim:sw=4:ts=4:et:
"""Python Ring RingGeneric wrapper."""
"""MUST USE PYTHON3 TO USE THIS"""
import logging
try:
    import asyncio
    import websockets
except ImportError:
    pass

import json
from datetime import datetime

from ring_doorbell.generic import RingGeneric
from ring_doorbell.props.devices import Device, Devices

_LOGGER = logging.getLogger(__name__)


try:
    import thread
except ImportError:
    import _thread as thread
import time


# Should put into class `Ring API Parser`
def parse_device(device_json):
    device = Device()

    try:
        v1_adapter_data = device_json['adapter']['v1']
        v1_data = device_json['device']['v1']
        v2_data = device_json['general']['v2']

        # Store unparsed data
        device._source_json = device_json
        device.name = v2_data['name']
        device.zid = v2_data['zid']
        device.batteryStatus = v2_data['batteryStatus']
        device.batteryLevel = v2_data.get('batteryLevel')
        device.categoryId = v2_data['categoryId']
        device.tamperStatus = v2_data['tamperStatus']
        device.tags = v2_data['tags']
        device.subCategoryId = v2_data['subCategoryId']
        device.roomId = v2_data['roomId']
        device.managerId = v2_data['managerId']
        device.lastUpdate = v2_data['lastUpdate']
        device.adapterType = v2_data['adapterType']
        device.adapterZid = v2_data.get('adapterZid')
        device.deviceType = v2_data['deviceType']
        device.deviceFoundTime = v2_data['deviceFoundTime']
        device.commandTypes = v2_data['commandTypes']
        device.commStatus = v2_data['commStatus']

        device.impulse_type = v2_data.get('impulseTypes')
        device.fingerprint = v2_data.get('fingerprint')
        device.faulted = v2_data.get('faulted')
        device.parent_zid = v2_data.get('parentZid')

        device.address = v1_adapter_data.get('address')
        device.fingerprint = v1_adapter_data.get('fingerprint')
        device.homeId = v1_adapter_data.get('homeId')
        device.nodeId = v1_adapter_data.get('nodeId')
        device.reconfigureState = v1_adapter_data.get('reconfigureState')
        device.routeSpeed = v1_adapter_data.get('routeSpeed')
        device.rssiTimestamp = v1_adapter_data.get('rssiTimestamp')
        device.signalStrength = v1_adapter_data.get('signalStrength')
    except KeyError as e:
        _LOGGER.debug('device_json: %s' % (device_json))
        raise e

    return device


def get_websocket_server(ring, location_id):
        url = 'https://app.ring.com/api/v1/clap/tickets?locationID=%s' % location_id

        _LOGGER.debug('url: %s' % (url))
        _LOGGER.debug('accountId: %s (Also known as "locationId")' % (location_id))

        response = ring.query(url)

        _LOGGER.debug('get_websocket_server response: %s' % (response))

        return response


class RingSecuritySystemProxy(object):
    def __init__(self, ring):
        self._ring = ring

    def get_websocket_server(self):
        location_id = self._ring.devices['doorbells'][0].location_id

        return get_websocket_server(self._ring, location_id)

    def get_socket_url(self):
        websocket_server = self.get_websocket_server()

        url = websocket_server['host']
        auth_code = websocket_server['ticket']
        self._ring.uuid = websocket_server['assets'][0]['uuid']
        self._ring.assets = websocket_server['assets']

        socket_url = 'wss://%s/socket.io/?authcode=%s&transport=websocket' % (url, auth_code)

        _LOGGER.debug('Socket URL: %s' % socket_url)

        return socket_url

    def get_devices(self):
        messages = [
            '42["message",{"msg":"RoomGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":1}]',
            '42["message",{"msg":"DeviceInfoDocGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":2}]'
        ]

        responses = self.connect_and_send_messages(messages)
        devices = Devices()

        device_jsons = json.loads(responses[2][2:])[1]['body']
        for device_json in device_jsons:
            device = parse_device(device_json)
            devices.add(device)

        return devices

    def set_lock(self, device, setting='lock'):
        msg = '42["message", {"msg": "DeviceInfoSet", "datatype": "DeviceInfoSetType", "body": [{"zid": "%s", "command": {"v1": [{"commandType": "lock.%s", "data": {}}]}}], "dst": "%s", "seq": 4}]' % (device.zid, setting, self._ring.uuid)

        messages = [msg]

        responses = self.connect_and_send_messages(messages)

        return True

    def connect_and_send_messages(self, messages):
        socket_url = self.get_socket_url()

        async def connect_to_websocket(socket_url, messages):
            async with websockets.connect(socket_url) as websocket:
                responses = []
                while(True):
                    result1 = await websocket.recv()
                    result2 = await websocket.recv()

                    for msg in messages:
                        await websocket.send(msg)

                    responses.append(await websocket.recv())
                    responses.append(await websocket.recv())
                    responses.append(await websocket.recv())

                    return responses


        return asyncio.get_event_loop().run_until_complete(connect_to_websocket(socket_url, messages))

    # def set_lock(self, device, lock_setting='lock'):
    #     socket_url = self.get_socket_url()

    #     async def connect_to_websocket(self, device, socket_url):
    #         async with websockets.connect(socket_url) as websocket:
    #             rec1 = await websocket.recv()
    #             rec2 = await websocket.recv()

    #             msg1 = '42["message", {"msg": "DeviceInfoSet", "datatype": "DeviceInfoSetType", "body": [{"zid": "%s", "command": {"v1": [{"commandType": "lock.%s", "data": {}}]}}], "dst": "%s", "seq": 4}]' % (device.zid, lock_setting, self._ring.uuid)
    #             await websocket.send(msg1)

    #             result3 = await websocket.recv()
    #             result4 = await websocket.recv()
    #             result5 = await websocket.recv()

    #             return

    #     asyncio.get_event_loop().run_until_complete(connect_to_websocket(self, device, socket_url))

    def maintain_connection(self):
        socket_url = self.get_socket_url()

        async def connect_to_websocket(socket_url):
            async with websockets.connect(socket_url) as websocket:
                while(True):
                    msg = await websocket.recv()

                    # This is Ring specific acknowledgement
                    #    After sending this, ring sends back '3'
                    if str(msg) == '2':
                        await websocket.send(msg)

        asyncio.get_event_loop().run_until_complete(connect_to_websocket(socket_url))
