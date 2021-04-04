import json
import logging
from datetime import datetime
from typing import Optional

import requests
from dateutil.tz import tzutc

logger = logging.getLogger()


class SimplyWallSt:

    def __init__(self, email: str, password: str, client_id: str = "90989a0528ad4b238480f1ac0f5855e5"):
        self.email = email
        self.password = password
        self._client_id = client_id
        self._refresh_token = None
        self._bearer_token = None

    def _get_access_tokens(self, refresh_token: Optional[str] = None):
        logger.info("Getting access tokens.")
        url = "https://api.simplywall.st/oauth/token"
        if refresh_token is None:
            form_data = {
                "client_id": self._client_id,
                "grant_type": "password",
                "password": self.password,
                "username": self.email,
                "scope": "public read:user write:user read:portfolio write:portfolio",
                "provider": "sws",
                "cross_client": "false"
            }
        else:
            form_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        r = requests.post(url, form_data)

        if r.status_code == 200:
            logger.info("Got access keys.")
        else:
            logger.warning(f"Something went wrong when getting the access keys: {r.text}")

        self._bearer_token, self._refresh_token = r.json()["access_token"], r.json()["refresh_token"]

    def get_portfolio_ticker_id(self, portfolio_id: str, exchange: str, ticker: str) -> Optional[int]:
        if self._bearer_token is None:
            self._get_access_tokens()

        logger.info(f"Getting portfolio ticker id for {exchange}:{ticker}.")
        url = "https://api.simplywall.st/api/user/portfolio?include=items&sharing=false"
        headers = {
            "Authorization": f"Bearer {self._bearer_token}"
        }

        response = requests.request("GET", url, headers=headers)

        portfolios = [portfolio for portfolio in response.json()["data"] if portfolio["id"] == int(portfolio_id)]

        if not len(portfolios) > 0:
            logger.warning(f"No portfolios when looking for ticker id for {exchange}:{ticker}.")
            return None

        positions = [position["id"] for position in portfolios[0]["items"]["data"] if position["unique_symbol"] == f"{exchange}:{ticker.upper()}"]

        if len(positions) > 1:
            raise Exception(f"Multiple positions matching {ticker.upper()} in portfolio {portfolio_id}")
        elif len(positions) < 1:
            logger.info(f"No portfolio ticker id for {exchange}:{ticker}.")
            return None

        return positions[0]

    def create_portfolio_ticker_id(self, portfolio_id: str, exchange: str, ticker: str):
        if self._bearer_token is None:
            self._get_access_tokens()

        logger.info(f"Create a portfolio ticker id for {exchange}:{ticker}.")
        url = f"https://api.simplywall.st/api/user/portfolio/item"
        headers = {
            "Authorization": f"Bearer {self._bearer_token}",
            "Content-Type": "application/json"
        }
        payload = json.dumps({
            "portfolio_id": portfolio_id,
            "unique_symbol": f"{exchange}:{ticker.upper()}"
        })
        r = requests.post(url, headers=headers, data=payload)

        if not r.status_code == 200:
            logger.warning(f"Could not create a portfolio ticker id for {exchange}:{ticker} because {r.text}.")

    def add_transaction(self, portfolio_ticker_id: int, transaction_type: str, transaction_date: datetime, shares: int, price: float):
        if self._bearer_token is None:
            self._get_access_tokens()

        url = "https://api.simplywall.st/api/user/portfolio/transaction"
        headers = {
            "Authorization": f"Bearer {self._bearer_token}"
        }

        epoch = datetime.fromtimestamp(0, tzutc())
        timestamp = int((datetime(transaction_date.year, transaction_date.month, transaction_date.day, tzinfo=tzutc()) - epoch).total_seconds() * 1000)

        form_data = {
            "item_id": f"{portfolio_ticker_id}",
            "type": "Buy" if transaction_type.upper() == "BUY" else "Sell",
            "date": timestamp,
            "amount": shares,
            "cost": price
        }

        r = requests.post(url, form_data, headers=headers)
        if not r.status_code == 200:
            logger.warning(f"Could not add transaction for {form_data} because {r.text}.")

    @staticmethod
    def get_exchange_ticker(exchange: str, ticker: str) -> Optional[str]:
        url = f"https://legacy.simplywall.st/api/search/{exchange}:{ticker.upper()}"
        response = requests.request("GET", url)

        tentatives = [tentative["value"] for tentative in response.json() if tentative["value"].replace(".", "") == f"{exchange}:{ticker.upper()}"]

        if len(tentatives) == 1:
            return tentatives[0]

        return None
