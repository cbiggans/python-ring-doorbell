import pdb;pdb.set_trace()
import logging
from datetime import datetime
from ring_doorbell.security import RingSecuritySystem

_LOGGER = logging.getLogger(__name__)


_LOGGER.info("Begin")
print("Begin")
security_system = RingSecuritySystem()
