# Trades Importer

[![PyPI version](https://badge.fury.io/py/trades-importer.svg)](https://badge.fury.io/py/trades-importer)

Trades Importer is a Python connector library that allows you to import your stock trading information into various services.  
It is available as PyPi [package](https://pypi.org/project/trades-importer/) installable with pip.

### Supported Services

* Simply Wall St.
* WallMine

## Simply Wall St.

![](.meta/simply_wall_st.png)

##### Authentication

You will need to have an account to use this service. You can sign up over [here](https://simplywall.st/register).  
The library supports **only** credentials based authentication(email/password) and not social login. If you have social login enabled, you can easily switch to credentials based authentication from the account preferences.

##### Portfolio

You will need to have a portfolio created before starting to use the library.  

It is best if you start with a **blank transactions portfolio**.  
When creating the portfolio for the first time, you will actually need to add at least one transaction. Add a dummy transaction, and after the portfolio is successfully created, remove said dummy transaction so you end up with an empty portfolio.  

The `portfolio_id` can easily be found by clicking on the portfolio in the interface in a browser and inspecting the URL. You will see something like this _https://simplywall.st/portfolio/my-portfolios/**477667889**/portfolio_name_.

##### Exchanges

The most difficult thing about using the connector is that when working with [tickers](https://en.wikipedia.org/wiki/Ticker_symbol), the corresponding exchange abbreviation is specific to _Simply Wall St._
  
For example, [Amyris](https://investors.amyris.com/stock-information) is listed on NASDAQ, but _Simply Wall St._ uses at least 3 symbols for NASDAQ: NasdaqCM, NasdaqCM, NasdaqGS.  
Since the connector doesn't maintain any mapping database, the correct exchange abbreviation needs to be determined at runtime and optionally cached by the client.  
A trivial example of how to determine the exchange ticker for `AMRS` is shown in the usage example below.

##### Other inconsistencies

The ticker for a company can change, you might need to handle this manually.  
As a rule of thumb, if a trade import fails, see if you can add it manually from the interface and note down the ticker/exchange pair and use it with the library.  

_Simply Wall St._ uses CDN protection, so try not to abuse the API, or you'll get kicked out at some point. It's fine most of the time. If that happens, you need to wait (I come back the next day, but maybe you can try in a few hours). 

##### Usage example

As a first step, you need to create an instance of the _Simply Wall St._ specific class. Email/password/portfolio need to be provided to the constructor.  

Before adding a transaction we need to make sure the exchange/ticker pair is recognized by _Simply Wall St._. The function `get_exchange_ticker` can help you do just that, if the provided trial pair can be associated in _Simply Wall St._ you'll get back the `exchange:ticker` pair as a string, or `None` otherwise.  
I strongly suggest you use the exchange/ticker returned by the helper function, it can be useful in cases where the ticker you provide is just slightly different Eg: `GOOGL` and `GOOG.L`.

Once you have the correct exchange/ticker pair, you need to fetch the corresponding `portfolio_ticker_id`. Each ticker is referenced by a unique ID in a given portfolio. To get this ID, use the `get_portfolio_ticker_id` method. However, this ID needs to have been created previously, so if you get `None` you'll need to create it before adding transactions corresponding to the ticker.  
To create a `portfolio_ticker_id` use the `create_portfolio_ticker_id` method. After this method is successfully executed, you can try again to get the `portfolio_ticker_id` using the `get_portfolio_ticker_id` method.

You are now finally ready to add transactions. Use the `add_transaction` method.  
The last argument to the method is `skip_duplicate`. This can help you achieve some sort of naive idempotence. However, in the _unlikely_ event of having two identical transactions, inconsistencies _might_ appear, depending on how you batch your transactions. All of this _might_ and _maybe_ and _probably_ is caused by the fact that currently the _Simply Wall St._ API does not support providing and retrieving custom transaction IDs.

```python
from datetime import datetime
from trades_importer import SimplyWallSt

simply_wall_st = SimplyWallSt(
    email="johndoe@gmail.com",
    password="jhsdjf%sdygs6sch",
    portfolio_id="477667889")

ex_ticker = SimplyWallSt.get_exchange_ticker(exchange="NasdaqCM", ticker="AMRS")
if ex_ticker is None:
    ex_ticker = SimplyWallSt.get_exchange_ticker(exchange="NasdaqGM", ticker="AMRS")

exchange = ex_ticker.split(":")[0]
ticker = ex_ticker.split(":")[1]

portfolio_ticker_id = simply_wall_st.get_portfolio_ticker_id(exchange=exchange, ticker=ticker)
if portfolio_ticker_id is None:
    simply_wall_st.create_portfolio_ticker_id(exchange=exchange, ticker=ticker)
    portfolio_ticker_id = simply_wall_st.get_portfolio_ticker_id(exchange=exchange, ticker=ticker)

simply_wall_st.add_transaction(
    portfolio_ticker_id=portfolio_ticker_id,
    transaction_type="Buy",
    transaction_date=datetime.today(),
    shares=10,
    price=20.10,
    skip_duplicate=True)
```
