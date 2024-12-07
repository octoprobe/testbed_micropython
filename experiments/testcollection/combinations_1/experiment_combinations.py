import itertools
import dataclasses


@dataclasses.dataclass(order=True, frozen=True, unsafe_hash=True)
class BoardVariant:
    board: str
    variant: str = ""

    @property
    def name(self):
        return f"{self.board}-{self.variant}"


board_variants = [
    BoardVariant("LolinD1"),
    BoardVariant("LolinC3"),
    BoardVariant("Pico2W"),
    BoardVariant("Pico2W", "RISCV"),
]

board_with_variants = ["Pico2W"]


combinations = list(itertools.combinations(board_variants, 2))
print("\n".join([str(x) for x in combinations]))


print("Remove combination which contains PICO2 twice:")


def same_board(a: BoardVariant, b: BoardVariant) -> bool:
    return a.board == b.board


combinations_different_boards = [c for c in combinations if not same_board(*c)]
print("\n".join([str(x) for x in combinations_different_boards]))

print("Put boards with variants left")


def flip(a: BoardVariant, b: BoardVariant) -> tuple[BoardVariant, BoardVariant]:
    if b.board in board_with_variants:
        return b, a
    return a, b


combinations_sorted = [flip(*c) for c in combinations_different_boards]
combinations_sorted.sort()
print("\n".join([str(x) for x in combinations_sorted]))
