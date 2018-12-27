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

_LOGGER.debug('ID: %s' % (ring.uuid))


# "context":{"affectedEntityType":"asset","
# affectedEntityId":"2851944a-c2a7-44cf-94dd-ae994ea38d46","accountId":"c23jb7-39ura-0","programId":"a551631c-0e88-4097-8e1a-9595202c2ba9","assetId":"2851944a-c2a7-44cf-94dd-ae994ea38d46","assetKind":"base_station_v1"}
