from quantlib_st.estimators.vol import robust_vol_calc


class DefaultForecastAlgo:
    @staticmethod
    def calc_ewmac_forecast(price, Lfast, Lslow=None):
        """
        Calculate the ewmac trading rule forecast, given a price and EWMA speeds
        Lfast, Lslow and vol_lookback

        """
        # price: This is the stitched price series
        # We can't use the price of the contract we're trading, or the volatility
        # will be jumpy
        # And we'll miss out on the rolldown. See
        # https://qoppac.blogspot.com/2015/05/systems-building-futures-rolling.html

        price = price.resample("1B").last()

        if Lslow is None:
            Lslow = 4 * Lfast

        # We don't need to calculate the decay parameter, just use the span
        # directly
        fast_ewma = price.ewm(span=Lfast).mean()
        slow_ewma = price.ewm(span=Lslow).mean()
        raw_ewmac = fast_ewma - slow_ewma

        vol = robust_vol_calc(price.diff())
        return raw_ewmac / vol
