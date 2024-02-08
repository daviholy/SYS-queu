import numpy as np

rng = np.random.default_rng()


def new_people() -> int:
    if not rng.random() > 0.8:
        return 0
    return rng.poisson(2)


def done() -> float:
    return rng.normal(15, 2) / 100
