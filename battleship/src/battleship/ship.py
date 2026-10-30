from enum import StrEnum


class ShipType(StrEnum):
    cruiser = "cruiser"
    carrier = "carrier"
    frigate = "frigate"


class Ship:
    id: str
    type: ShipType
    size: int = 3

    def __repr__(self) -> str:
        return f"{self.id} - ({self.type})"
