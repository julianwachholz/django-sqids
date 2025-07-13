import random

from sqids.constants import DEFAULT_ALPHABET

from .field import shuffle_alphabet

if __name__ == '__main__':
    random_seed = random.random()
    shuffled_alphabet = shuffle_alphabet(seed=random_seed, alphabet=DEFAULT_ALPHABET)
    print(shuffled_alphabet)
