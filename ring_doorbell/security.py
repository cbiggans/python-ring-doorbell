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
from ring_doorbell.props.devices import Devices

_LOGGER = logging.getLogger(__name__)


try:
    import thread
except ImportError:
    import _thread as thread
import time

# def on_message(ws, message):
#     print(message)
# 
# def on_error(ws, error):
#     print(error)
# 
# def on_close(ws):
#     print("### closed ###")
# 
# def on_open(ws):
#     def run(*args):
#         for i in range(3):
#             time.sleep(1)
#             ws.send("Hello %d" % i)
#         time.sleep(1)
#         ws.close()
#         print("thread terminating...")
#     thread.start_new_thread(run, ())


class RingSecuritySystem(RingGeneric):
    """Implementation for Ring Security System."""

    def __init__(self, ring, name, shared=False):
        super(RingSecuritySystem, self).__init__(ring, name, shared=False)

        try:
            from ring_doorbell.security_proxy import RingSecuritySystemProxy
            self._attrs = {
                'location_id': self._ring.devices['doorbells'][0].location_id,
                'uuid': None,
                'auth_code': None,
                'assets': None,
            }
            self.proxy = RingSecuritySystemProxy(self)
        except SyntaxError:
            raise(ImportError("Must use python version >=3.4"))

        self.devices = Devices()

    def get_devices(self):
        self.devices = self.proxy.get_devices()

        return self.devices

    def set_alarm(self, mode='none'):
        """
        mode=['none', 'some', 'all']

        'none' refers to 'Disarmed'
        'some' refers to 'Home & Armed'
        'all' refers to 'Away & Armed'
        """
        return self.proxy.set_alarm(self.zid, self.uuid, mode)

    def set_lock(self, device, setting='lock'):
        """
        setting=['lock', 'unlock']
        """
        return self.proxy.set_lock(device, setting=setting)

    def connect_and_send_messages(self, messages):
        return self.proxy.connect_and_send_messages(messages)

    @property
    def id(self):
        pass

    @property
    def zid(self):
        return self.devices.get_security_panel()[0].zid
