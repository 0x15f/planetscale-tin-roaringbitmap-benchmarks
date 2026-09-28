"""Deterministic synthetic corpus with logical IDs above 2**32."""
import hashlib
import random

SEED = 20260926
BASE = 2**40
SELECTIVITIES = [1, .75, .5, .25, .1, .05, .01, .001, 0]


def documents(n):
    rng = random.Random(SEED)
    for i in range(n):
        strength = rng.random()
        words = ['catalog', 'product']
        if strength < .8: words += ['common'] * (1 + int((.8-strength)*10))
        if strength < .2: words += ['medium']
        if strength < .005: words += ['rare']
        if i % 3 == 0: words += ['blue', 'ocean']
        words += [f'topic{i % 100}', f'group{i % 17}']
        text = ' '.join(words)
        yield (BASE+i, i % 100, i % 4, i % 20, i % 5 != 0, f'Product {i}', text, text)


def digest(rows):
    return hashlib.sha256('\n'.join(repr(row) for row in rows).encode()).hexdigest()


def eligibility(rows):
    n = len(rows)
    rng = random.Random(SEED + 1)
    random_ids = [r[0] for r in rows]
    rng.shuffle(random_ids)
    positive = sorted(rows, key=lambda r: (-r[-1].split().count('common'), r[0]))
    negative = list(reversed(positive))
    for fraction in SELECTIVITIES:
        count = int(n * fraction)
        for kind, ids in [('random', random_ids), ('clustered', [r[0] for r in rows]),
                          ('positive', [r[0] for r in positive]), ('negative', [r[0] for r in negative])]:
            yield f'{kind}_{fraction:g}', sorted(ids[:count]), {'kind': kind, 'fraction': fraction}
    for name, test in [('tenant', lambda r:r[1]==0), ('channel', lambda r:r[2]==0),
                       ('category', lambda r:r[3]==0), ('active', lambda r:r[4]),
                       ('combined', lambda r:r[1]==0 and r[2]==0 and r[4])]:
        yield name, [r[0] for r in rows if test(r)], {'kind': name}
