import os
import sys
import logging
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '%s/../' % (current_dir))

from ring_doorbell.security import RingSecuritySystem
from ring_doorbell import Ring

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Begin")

username = os.environ.get('RING_USERNAME', 'username')
password = os.environ.get('RING_PASSWORD', 'password')

ring = Ring(username, password)
security_system = ring.security_system
devices = security_system.get_devices()

security_system.proxy.set_lock(devices.get_locks()[0], setting='unlock')

# _LOGGER.debug('ID: %s' % (security_system.uuid))
