# coding: utf-8
# vim:sw=4:ts=4:et:
"""Python Ring RingGeneric wrapper."""
import logging
import asyncio
import websockets
import websocket
import json
from datetime import datetime

from ring_doorbell.generic import RingGeneric

_LOGGER = logging.getLogger(__name__)


try:
    import thread
except ImportError:
    import _thread as thread
import time

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        for i in range(3):
            time.sleep(1)
            ws.send("Hello %d" % i)
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())

class Devices(object):
    # Collection of Devices
    def __init__(self):
        self.devices = []
    
    def add(self, device):
        self.devices.append(device)

    def get_contact_sensors(self):
        result = []
        for device in self.devices:
            if device.deviceType == 'sensor.contact':
                result.append(device)
        return result

    def get_motion_sensors(self):
        result = []
        for device in self.devices:
            if device.deviceType == 'sensor.motion':
                result.append(device)
        return result

    def get_alarms(self):
        result = []
        for device in self.devices:
            if 'alarm' in device.deviceType:
                result.append(device)
        return result

    def get_access_codes(self):
        result = []
        for device in self.devices:
            if 'access-code' in device.deviceType:
                result.append(device)
        return result

    def get_security_panel(self):
        result = []
        for device in self.devices:
            if 'security-panel' in device.deviceType:
                result.append(device)
        return result

    def get_hubs(self):
        result = []
        for device in self.devices:
            if 'hub' in device.deviceType:
                result.append(device)
        return result

    def get_locks(self):
        result = []
        for device in self.devices:
            if 'lock' in device.deviceType:
                result.append(device)
        return result

    def get_range_extenders(self):
        result = []
        for device in self.devices:
            if 'range-extender' in device.deviceType:
                result.append(device)
        return result


class Device(object):
    def __init__(self, device_collection):
        self.id = None
        self._source_json = None
        self.device_collection = device_collection

    def get_children(self):
        result = []
        for device in self.device_collection.devices:
            if device.parent_zid == self.zid:
                result.append(device)

        return result

class RingSecuritySystem(RingGeneric):
    """Implementation for Ring Security System."""

    def __init__(self, ring, name, shared=False):
        super(RingSecuritySystem, self).__init__(ring, name, shared=False)

        self.devices = Devices()

    def get_socket_url(self):
        websocket_server = self.get_websocket_server()

        url = websocket_server['server']
        auth_code = websocket_server['authCode']

        socket_url = 'wss://%s/socket.io/?authcode=%s&transport=websocket' % (url, auth_code)

        _LOGGER.debug('Socket URL: %s' % socket_url)

        return socket_url

    # TODO XXX
    def connect_and_send_msg(self, msg):
        socket_url = self.get_socket_url()
        devices = None

        async def connect_to_websocket(socket_url):
            async with websockets.connect(socket_url) as websocket:
                while(True):
                    # msg = await websocket.recv()
                    # print(f"< {msg}")

                    result1 = await websocket.recv()
                    print(f"< {result1}")
                    result2 = await websocket.recv()
                    print(f"< {result2}")

                    msg1 = '42["message",{"msg":"RoomGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":1}]'
                    await websocket.send(msg1)
                    print(f"> {msg1}")

                    msg2 = '42["message",{"msg":"DeviceInfoDocGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":2}]'
                    await websocket.send(msg2)
                    print(f"> {msg2}")

                    result3 = await websocket.recv()
                    print(f"< {result3}")
                    result4 = await websocket.recv()
                    print(f"< {result4}")
                    result5 = await websocket.recv()
                    print(f"< {result5}")

                    devices = json.loads(result5[2:])[1]['body']
                    for device in devices:
                        self.load_device(device)

                    import pdb;pdb.set_trace()
                    return result5

        asyncio.get_event_loop().run_until_complete(connect_to_websocket(socket_url))


    # Should put into class `Ring API Parser`
    def load_device(self, device_json):
        device = Device(self.devices)

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

        self.devices.add(device)

    def maintain_connection(self):
        socket_url = self.get_socket_url()

        async def connect_to_websocket(socket_url):
            async with websockets.connect(socket_url) as websocket:
                while(True):
                    msg = await websocket.recv()
                    print(f"< {msg}")

                    # This is Ring specific acknowledgement
                    #    After sending this, ring sends back '3'
                    if str(msg) == '2':
                        await websocket.send(msg)
                        print(f"> {msg}")

        asyncio.get_event_loop().run_until_complete(connect_to_websocket(socket_url))

    def get_websocket_server(self):
        url = 'https://app.ring.com/api/v1/rs/connections'
        location_id = self._ring.devices['doorbells'][0].location_id

        _LOGGER.debug('url: %s' % (url))
        _LOGGER.debug('accountId: %s' % (location_id))

        response = self._ring.query(
                (url), method='POST',
                data={'accountId': location_id})

        _LOGGER.debug('get_websocket_server response: %s' % (response))
        return response

    @property
    def id(self):
        pass
