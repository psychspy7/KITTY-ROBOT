from cadgen import step
from finish import part
from settings import load
from shapes import electronics_deck


@step(out='../STEP/v3_electronics_deck.step')
def v3_electronics_deck():
    p = load()
    return part(electronics_deck(p), p)


if __name__ == '__main__':
    v3_electronics_deck()
