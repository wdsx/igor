from enum import Enum


class EnvironmentTier(Enum):
    WORKER = 'worker'
    WEB_SERVER = 'web_server'