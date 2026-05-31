import re
from src.building_blocks.domain.rule import BaseBusinessRule


class DeviceHashMustBeValidSha256Rule(BaseBusinessRule):
    device_hash: str
    code: str = "DeviceHashMustBeValidSha256"
    message: str = "Device hash must be a valid 64-character SHA-256 hexadecimal string."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if not self.device_hash:
            return True
        return not bool(re.match(r"^[a-fA-F0-9]{64}$", self.device_hash))
