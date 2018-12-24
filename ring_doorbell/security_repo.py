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

    return device


class RingSecuritySystemRepo(object):
    def __init__(self, ring):
        self._ring = ring

    def get_websocket_server(self):
        url = 'https://app.ring.com/api/v1/rs/connections'
        location_id = self._ring.devices['doorbells'][0].location_id

        _LOGGER.debug('url: %s' % (url))
        _LOGGER.debug('accountId: %s' % (location_id))

        response = self._ring.query(
                (url), method='POST',
                data={'accountId': location_id},
                get_post_json=True)

        _LOGGER.debug('get_websocket_server response: %s' % (response))
        return response

    def get_socket_url(self):
        websocket_server = self.get_websocket_server()

        url = websocket_server['server']
        auth_code = websocket_server['authCode']

        socket_url = 'wss://%s/socket.io/?authcode=%s&transport=websocket' % (url, auth_code)

        _LOGGER.debug('Socket URL: %s' % socket_url)

        return socket_url

    def connect_and_send_msg(self, msg):
        socket_url = self.get_socket_url()
        devices = Devices()

        async def connect_to_websocket(socket_url):
            async with websockets.connect(socket_url) as websocket:
                while(True):
                    # msg = await websocket.recv()
                    # print(f"< {msg}")

                    result1 = await websocket.recv()
                    result2 = await websocket.recv()

                    msg1 = '42["message",{"msg":"RoomGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":1}]'
                    await websocket.send(msg1)

                    msg2 = '42["message",{"msg":"DeviceInfoDocGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":2}]'
                    await websocket.send(msg2)

                    result3 = await websocket.recv()
                    result4 = await websocket.recv()
                    result5 = await websocket.recv()

                    device_jsons = json.loads(result5[2:])[1]['body']
                    for device_json in device_jsons:
                        device = parse_device(device_json)
                        devices.add(device)

                    return devices


        asyncio.get_event_loop().run_until_complete(connect_to_websocket(socket_url))
        return devices


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
