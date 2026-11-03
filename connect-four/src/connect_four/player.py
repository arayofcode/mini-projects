from src.connect_four.board import DiscColor


class Player:
    name: str
    disc: DiscColor

    def __init__(self, name: str, disc: DiscColor) -> None:
        self.name = name
        self.disc = disc

    def get_name(self) -> str:
        return self.name

    def get_color(self) -> DiscColor:
        return self.disc
