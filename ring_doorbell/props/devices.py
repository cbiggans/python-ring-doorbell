

class Devices(object):
    # Collection of Devices
    def __init__(self):
        self.devices = []
    
    def add(self, device):
        device.device_collection = self

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
    def __init__(self, device_collection=None):
        self.id = None
        self._source_json = None
        self.device_collection = device_collection

    def get_children(self):
        result = []
        for device in self.device_collection.devices:
            if device.parent_zid == self.zid:
                result.append(device)

        return result

    def get_parent(self):
        for device in self.device_collection.devices:
            if device.zid == self.parent_zid:
                return device

        return None
