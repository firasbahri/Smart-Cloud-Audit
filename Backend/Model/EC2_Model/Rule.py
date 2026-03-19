
class Rule:
    def __init__(self, protocol, from_port, to_port, ip_ranges):
        self.protocol = protocol
        self.from_port = from_port
        self.to_port = to_port
        self.ip_ranges = ip_ranges
