from enum import Enum

class DeviceType(str, Enum):
    IOT = "iot"
    ROBOT = "robot"
    MEDICAL = "medical"
    CAMERA = "camera"
    EDGE = "edge"
    ENTERPRISE = "enterprise"
    SMART_HOME = "smart_home"
    WEARABLE = "wearable"
    NETWORK = "network"
    UNKNOWN = "unknown"


class DeviceCapability(str, Enum):
    SENSOR = "sensor"           # Data collection
    ACTUATOR = "actuator"       # Physical action
    CAMERA = "camera"           # Visual input
    NETWORK = "network"         # Network monitoring
    MEDICAL = "medical"         # Medical devices
    ENTERPRISE = "enterprise"   # Enterprise systems
    STORAGE = "storage"         # Storage devices
    COMPUTE = "compute"         # Edge compute


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    PENDING = "pending"
    UNKNOWN = "unknown"


class DeviceTrustLevel(str, Enum):
    FULL = "full"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNTRUSTED = "untrusted"
