import logging
from datetime import datetime
from ring_doorbell.security import RingSecuritySystem
from ring_doorbell import Ring

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("Begin")

ring = Ring('username', 'password')
security_system = ring.security_system


_LOGGER.debug('ID: %s' % (security_system.id))
