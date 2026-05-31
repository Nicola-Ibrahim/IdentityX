import ipaddress
from src.building_blocks.domain.rule import BaseBusinessRule


class IpAddressMustBeValidRule(BaseBusinessRule):
    ip_address: str
    code: str = "InvalidIpAddress"
    message: str = "IP address must be a valid IPv4 or IPv6 address."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        try:
            ipaddress.ip_address(self.ip_address)
            return False
        except ValueError:
            return True
