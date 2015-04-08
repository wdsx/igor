import ConfigParser


class Tenant():
    def __init__(self):
        self.config = ConfigParser.ConfigParser()

    def load_properties(self, project_name=None):
        self.config.read('igor.ini')

    def get_property(self, name, default=None):
        try:
            value = self.config.get('igor', name)
            if value is None:
                return default
        except ConfigParser.NoOptionError:
            return default
        return self.config.get('igor', name)
