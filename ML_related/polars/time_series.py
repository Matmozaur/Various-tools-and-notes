from datetime import datetime

import pandas as pd
import polars as pl


if __name__ == '__main__':
    df_polars = pl.DataFrame(
        {
            "datetime": [
                datetime(2021,1,1), datetime(2021,1,2), datetime(2021,1,3)
            ],
            "value": [1, 2, 3]
        }
    )
    df_pandas = df_polars.to_pandas()
    print(df_polars)

    print("Filtering")
    print(df_polars.filter(pl.col("datetime") > datetime(2021,1,2)))

    # In Pandas the integer counts occur in nanoseconds by default but in Polars the integer counts occur in microseconds by default.
    df_polars = pl.from_pandas(df_pandas).with_columns(pl.col("datetime").dt.cast_time_unit("us"))

    df_polars2 = pl.DataFrame(
        {
            "datetime": [
                datetime(2021, 1, 1), None, datetime(2021, 1, 3)
            ],
            "value": [1, 2, 3]
        }
    )
    print("Nulls")
    print(df_polars2)


    print('Aggr:')
    print(df_pandas.set_index("datetime").groupby(pd.Grouper(freq='D')).mean())
    print(df_polars.sort("datetime").group_by_dynamic("datetime", every="1d").agg(pl.col("value").mean()))

    print("Sampling")
    print(df_polars.sort("datetime").upsample("datetime", every="30m"))
