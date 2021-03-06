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
        device.battery_status = v2_data['batteryStatus']
        device.battery_level = v2_data.get('batteryLevel')
        device.category_id = v2_data['categoryId']
        device.tamper_status = v2_data['tamperStatus']
        device.tags = v2_data['tags']
        device.sub_category_id = v2_data['subCategoryId']
        device.room_id = v2_data['roomId']
        device.manager_id = v2_data['managerId']
        device.last_update = v2_data['lastUpdate']
        device.adapter_type = v2_data['adapterType']
        device.adapter_zid = v2_data.get('adapterZid')
        device.device_type = v2_data['deviceType']
        device.device_found_time = v2_data['deviceFoundTime']
        device.comm_status = v2_data['commStatus']

        # If the status is broken, then does not have this setting
        device.command_types = v2_data.get('commandTypes')

        device.impulse_type = v2_data.get('impulseTypes')
        device.fingerprint = v2_data.get('fingerprint')
        device.parent_zid = v2_data.get('parentZid')

        device.address = v1_adapter_data.get('address')
        device.fingerprint = v1_adapter_data.get('fingerprint')
        device.home_id = v1_adapter_data.get('homeId')
        device.node_id = v1_adapter_data.get('nodeId')
        device.reconfigure_state = v1_adapter_data.get('reconfigureState')
        device.route_speed = v1_adapter_data.get('routeSpeed')
        device.rssi_timestamp = v1_adapter_data.get('rssiTimestamp')
        device.signal_strength = v1_adapter_data.get('signalStrength')

        # Lock Specific
        device.lock_setting = v1_data.get('locked')

        # Contact Sensor Specific
        device.faulted = v1_data.get('faulted')

        # Security Panel Specific
        device.mode = v1_data.get('mode')

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
    def __init__(self, security_system):
        self._security_system = security_system

    def get_websocket_server(self):
        location_id = self._security_system.location_id

        return get_websocket_server(self._security_system._ring, location_id)

    def get_socket_url(self):
        websocket_server = self.get_websocket_server()

        url = websocket_server['host']
        self._security_system._attrs['auth_code'] = websocket_server['ticket']
        self._security_system._attrs['uuid'] = websocket_server['assets'][0]['uuid']
        self._security_system._attrs['assets'] = websocket_server['assets']

        socket_url = 'wss://%s/socket.io/?authcode=%s&transport=websocket' % (
            url, self._security_system.auth_code)

        _LOGGER.debug('Socket URL: %s' % socket_url)

        return socket_url

    def get_devices(self):
        messages = [
            '42["message",{"msg":"RoomGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":1}]',
            '42["message",{"msg":"DeviceInfoDocGetList","dst":"2851944a-c2a7-44cf-94dd-ae994ea38d46","seq":2}]'
        ]

        responses = self.connect_and_send_messages(messages)
        devices = Devices()

        try:
            # TODO XXX: Refactor this out, shouldn't have this logic in here for testing
            #   purposes
            loaded_data = None
            for response in responses:
                tmp_loaded_data = json.loads(response[2::])
                if (tmp_loaded_data[1].get('datatype') == 'DeviceInfoDocType' and
                    tmp_loaded_data[1].get('msg') == 'DeviceInfoDocGetList'):
                    loaded_data = tmp_loaded_data
                    break

            # TODO XXX: See if can just wait for msg type needed when calling
            #   get_messages

            device_jsons = loaded_data[1]['body']
            for device_json in device_jsons:
                device = parse_device(device_json)
                devices.add(device)
        except KeyError as e:
            import pdb;pdb.set_trace()
            raise e
        except TypeError as e:
            import pdb;pdb.set_trace()
            raise e

        return devices

    def set_lock(self, device, setting='lock'):
        msg = '42["message", {"msg": "DeviceInfoSet", "datatype": "DeviceInfoSetType", "body": [{"zid": "%s", "command": {"v1": [{"commandType": "lock.%s", "data": {}}]}}], "dst": "%s", "seq": 4}]' % (device.zid, setting, self._security_system.uuid)

        messages = [msg]

        responses = self.connect_and_send_messages(messages)

        return True

    def set_alarm(self, zid, uuid, mode):
        """
        setting=['none', 'some', 'all']
        """
        # modes = {
        #     'disarmed': 'none',
        #     'home':     'some',
        #     'away':     'all',
        # }

        msg = '42["message",{"msg":"DeviceInfoSet","datatype":"DeviceInfoSetType","body":[{"zid":"%s","command":{"v1":[{"commandType":"security-panel.switch-mode","data":{"mode":"%s"}}]}}],"dst":"%s","seq":3}]' % (
            zid, mode, uuid)

        messages = [msg]

        responses = self.connect_and_send_messages(messages)

        # TODO XXX: Refactor this out, shouldn't have this logic in here for testing
        #   purposes
        loaded_data = None
        for response in responses:
            tmp_loaded_data = json.loads(response[2::])
            if tmp_loaded_data[0] == 'DataUpdate':
                if tmp_loaded_data[1].get('datatype') == 'DeviceInfoDocType':
                    loaded_data = tmp_loaded_data
                    break
                elif tmp_loaded_data[1].get('datatype') == 'PassthruType':
                    loaded_data = tmp_loaded_data
                    break

        try:
            message_data = loaded_data[1]['body'][0]
        except Exception as e:
            _LOGGER.debug('responses: %s' % (responses))
            _LOGGER.debug('loaded_data: %s' % (loaded_data))
            import pdb;pdb.set_trace()
            raise e

        # Countdown normally happens in 'AWAY' mode
        if message_data.get('type') and 'countdown' in message_data['type']:
            status = {
                'mode': mode,
                'error': False,
                'mode_changed': True,
                'in_countdown': True,
            }
            responses.append(json.dumps(status))
            return responses

        try:
            impulse_data = message_data['impulse']['v1'][0]
            impulse_type = impulse_data['impulseType']
            status = {
                "mode_changed": None,
                "error": None,
                "mode": impulse_type.split('.')[-1],
                "in_countdown": False,
            }
        except Exception as e:
            _LOGGER.debug('message_data: %s' % (message_data))
            raise e

        if status['mode'] == mode:
            status["mode_changed"] = True
            status["error"] = False
        else:
            status["mode_changed"] = False
            # An error didn't occur if the mode didn't change
            status["error"] = False if impulse_type == 'command.complete' else True
            status["mode"] = mode

        responses.append(json.dumps(status))

        return responses

    def connect_and_send_messages(self, messages, min_num_messages=3):
        socket_url = self.get_socket_url()

        async def connect_to_websocket(socket_url, messages):
            async with websockets.connect(socket_url) as websocket:
                responses = []
                while(True):
                    result1 = await websocket.recv()
                    result2 = await websocket.recv()

                    for msg in messages:
                        await websocket.send(msg)

                    async def tmp(responses):
                        while(True):
                            responses.append(await websocket.recv())

                    responses = []
                    try:
                        # Wait 3 seconds so that can be sure to get all of the messages
                        await asyncio.wait_for(tmp(responses), timeout=3)
                        # Better way might be to check if got the correct
                        # message was looking for?
                    except asyncio.TimeoutError:
                        pass

                    return responses


        return asyncio.get_event_loop().run_until_complete(connect_to_websocket(socket_url, messages))

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
