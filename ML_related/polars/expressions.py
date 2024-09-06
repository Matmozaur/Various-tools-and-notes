import polars as pl
import numpy as np


if __name__ == '__main__':
    df = pl.scan_csv('hotels-europe_price.csv')
    print(df.head().collect())


    #
    print("select")
    print(df.select([
            pl.col('hotel_id'),
            pl.col('year'),
            pl.col('price'),
            pl.col('offer_cat')
        ]).collect())
    print('\n')

    # with_columns
    print('with_columns')
    print(df.with_columns(
            random_breakfast=pl.Series(
                np.random.choice([0, 1], len(df.select(pl.col("hotel_id")).collect()))
            ),
            breakfast=pl.lit(1),
        ).select(pl.col('hotel_id'), pl.col('breakfast'), pl.col('random_breakfast')).collect())
    print('\n')

    # filter
    print('filter')
    print(df.filter(
            (pl.col('year') != 2018) &
            (pl.col('price') > 2500) &
            (pl.col('price') < 2600) &
            (
                (pl.col('offer_cat') == "50%-75% offer") |
                (pl.col('offer_cat') == "0% no offer")
            )
        ).collect())
    print('\n')

    # group_by
    print('\n')
    print(df.group_by(['hotel_id', 'year'],maintain_order=True).agg(
            pl.col('price').mean().alias('avg_price'),
            pl.col('price').min().alias('min_price'),
            pl.col('price').max().alias('max_price'),
            pl.col('price').n_unique().alias('n_prices')
        ).head(15).collect())
    print('\n')


    # complex expression
    print('complex example')
    df_len = df.select(pl.len()).collect().item(0, 0)
    print(df.with_columns(
                is_breakfast = pl.Series(np.random.choice([0, 1], df_len)),
                is_premium_location = pl.Series(np.random.choice([0, 1], df_len)),
                total_price = pl.col('price') * pl.col('nnights')
            ).filter(
                (pl.col('is_breakfast') == 1) &
                (pl.col('is_premium_location') == 1) &
                (
                    (pl.col('total_price') >= 1000) |
                    (pl.col('price') > 1000)
                ) &
                (pl.col('year') == 2018) &
                (pl.col('month').is_in([1, 2, 3, 4, 5, 6]))
            ).select(
                'hotel_id',
                'year',
                'month',
                'price',
                'total_price',
                'is_breakfast',
                'is_premium_location',
                'offer_cat'
            ).sort(by='total_price', descending=True).collect())
