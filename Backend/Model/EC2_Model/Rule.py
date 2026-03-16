
class Rule:
    def __init__(self, protocol, from_port, to_port, ip_ranges):
        self.protocol = protocol
        self.from_port = from_port
        self.to_port = to_port
        self.ip_ranges = ip_ranges

    def get_protocol(self):
        return self.protocol

    def get_from_port(self):
        return self.from_port

    def get_to_port(self):
        return self.to_port

    def get_ip_ranges(self):
        return self.ip_ranges