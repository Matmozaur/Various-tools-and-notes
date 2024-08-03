import time

import numpy as np
import pandas as pd
import polars as pl

if __name__ == '__main__':
    num_rows = 5000
    rng = np.random.default_rng(seed=7)

    buildings_data = {
          "sqft": rng.exponential(scale=1000, size=num_rows),
          "year": rng.integers(low=1995, high=2023, size=num_rows),
          "building_type": rng.choice(["A", "B", "C"], size=num_rows),
      }
    buildings = pl.DataFrame(buildings_data)
    print(buildings)
    print(buildings.schema)
    print(buildings.describe())

    print(buildings.select(pl.col("sqft").sort() / 1000))
    print('\n ------------------ \n')

    num_rows = 100000
    buildings_data_big = {
        "sqft": rng.exponential(scale=1000, size=num_rows),
        "year": rng.integers(low=1995, high=2023, size=num_rows),
        "building_type": rng.choice(["A", "B", "C"], size=num_rows),
    }
    buildings_pl = pl.DataFrame(buildings_data_big)
    buildings_pd = pd.DataFrame(buildings_data_big)

    start = time.time()
    buildings_pd.describe()
    print(f'Describe time pd: {time.time() - start}')

    start = time.time()
    buildings_pl.describe()
    print(f'Describe time pl: {time.time() - start}')

    start = time.time()
    buildings_pd['sqft'].sort_values()
    print(f'Sort time pd: {time.time() - start}')

    start = time.time()
    buildings_pl.select(pl.col("sqft").sort())
    print(f'Sort time pl: {time.time() - start}')
