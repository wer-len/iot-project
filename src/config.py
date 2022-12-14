from configparser import ConfigParser


class Config:
    def __init__(self):
        self.filename = 'config.ini'
        self.config = ConfigParser()
        self.load()

    @property
    def opcua_address(self):
        return self.config.get('opcua', 'address')

    def load(self):
        self.config.read(self.filename)
        new_config = False

        if not self.config.has_section('opcua'):
            self.config.add_section('opcua')
            new_config = True

        if not self.config.has_option('opcua', 'address'):
            self.config.set('opcua', 'address', input('Adres serwera OPC UA: '))
            new_config = True

        if not self.config.has_section('devices'):
            self.config.add_section('devices')
            new_config = True

        if new_config:
            self.save()

    def save(self):
        with open(self.filename, 'w') as f:
            self.config.write(f)

    def get_device_connection_string(self, section: str, device: str):
        if not self.config.has_option(section, device):
            self.config.set(section, device, input(f'Adres urządzenia {device}: '))
            self.save()

        return self.config.get(section, device)