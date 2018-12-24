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
        try:
            from ring_doorbell.security_repo import RingSecuritySystemRepo
        except SyntaxError:
            raise(BaseException("Must use python version >=3.4"))

        super(RingSecuritySystem, self).__init__(ring, name, shared=False)
        from ring_doorbell.props.devices import Devices

        self.devices = Devices()

    def get_devices(self):
        devices = self.connect_and_send_msg('RoomGetList')

        return devices

    def connect_and_send_msg(self, msg):
        from ring_doorbell.security_repo import RingSecuritySystemRepo

        repo = RingSecuritySystemRepo(self._ring)

        return repo.connect_and_send_msg(msg)

    @property
    def id(self):
        pass
