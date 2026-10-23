from cadgen import step
from finish import part
from settings import load
from shapes import electronics_deck


@step(out='../STEP/r2_electronics_deck.step')
def r2_electronics_deck():
    p = load()
    return part(electronics_deck(p), p)


if __name__ == '__main__':
    r2_electronics_deck()
