import json
import logging
from datetime import datetime
from typing import Optional, List, Dict

import requests
from dateutil.tz import tzutc

logger = logging.getLogger()


class SimplyWallSt:

    def __init__(self, email: str, password: str, portfolio_id: str, client_id: str = "90989a0528ad4b238480f1ac0f5855e5"):
        self.email = email
        self.password = password
        self._client_id = client_id
        self._bearer_token = None
        self.transactions = None
        self.portfolio_id = portfolio_id

    def _get_access_tokens(self):
        logger.info("Getting access tokens.")
        url = "https://api.simplywall.st/oauth/token"
        form_data = {
            "client_id": self._client_id,
            "grant_type": "password",
            "password": self.password,
            "username": self.email,
            "scope": "public read:user write:user read:portfolio write:portfolio",
            "provider": "sws",
            "cross_client": "false"
        }
        response = requests.post(url, form_data)

        if response.status_code == 200:
            logger.info("Got access keys.")
        else:
            logger.warning(f"Something went wrong when getting the access keys: {response.text}")

        self._bearer_token = response.json()["access_token"]

    def get_portfolio_ticker_id(self, exchange: str, ticker: str) -> Optional[int]:
        if self._bearer_token is None:
            self._get_access_tokens()

        logger.info(f"Getting portfolio ticker id for {exchange}:{ticker}.")
        url = "https://api.simplywall.st/api/user/portfolio?include=items"
        headers = {
            "Authorization": f"Bearer {self._bearer_token}"
        }

        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Something went wrong when trying to get the portfolio ticker id for {exchange}:{ticker}. Code {response.status_code}")
            return None

        portfolios = [portfolio for portfolio in response.json()["data"] if portfolio["id"] == int(self.portfolio_id)]

        if not len(portfolios) > 0:
            logger.warning(f"No portfolios when looking for ticker id for {exchange}:{ticker}.")
            return None

        positions = [position["id"] for position in portfolios[0]["items"]["data"] if position["unique_symbol"] == f"{exchange}:{ticker.upper()}"]

        if len(positions) > 1:
            raise Exception(f"Multiple positions matching {ticker.upper()} in portfolio {self.portfolio_id}")
        elif len(positions) < 1:
            logger.info(f"No portfolio ticker id for {exchange}:{ticker}.")
            return None

        return positions[0]

    def create_portfolio_ticker_id(self, exchange: str, ticker: str):
        if self._bearer_token is None:
            self._get_access_tokens()

        logger.info(f"Create a portfolio ticker id for {exchange}:{ticker}.")
        url = f"https://api.simplywall.st/api/user/portfolio/item"
        headers = {
            "Authorization": f"Bearer {self._bearer_token}",
            "Content-Type": "application/json"
        }
        payload = json.dumps({
            "portfolio_id": self.portfolio_id,
            "unique_symbol": f"{exchange}:{ticker.upper()}"
        })
        response = requests.post(url, headers=headers, data=payload)

        if not response.status_code == 200:
            logger.warning(f"Could not create a portfolio ticker id for {exchange}:{ticker} because {response.text}.")

    def get_existing_transactions(self) -> Optional[List[Dict]]:
        if self._bearer_token is None:
            self._get_access_tokens()

        transactions = []

        logger.info("Getting existing transactions.")
        url = "https://api.simplywall.st/api/user/portfolio?include=items.transactions"

        headers = {
            "Authorization": f"Bearer {self._bearer_token}"
        }

        response = requests.request("GET", url, headers=headers)

        if response.status_code == 200:
            logger.info("Got transactions for all portfolios.")
        else:
            logger.warning(f"Something went wrong when getting the transactions.")

        portfolios = [portfolio for portfolio in response.json()["data"] if portfolio["id"] == int(self.portfolio_id)]
        if not len(portfolios) > 0:
            logger.warning(f"No portfolios found for {self.portfolio_id}.")
            return None

        for item in portfolios[0]["items"]["data"]:
            for transaction in item["transactions"]["data"]:
                transactions.append({
                    "item_id": f"{transaction['item_id']}",
                    "type": transaction["type"],
                    "date": transaction["date"],
                    "amount": int(transaction["amount"]),
                    "cost": transaction["cost"]
                })

        return transactions

    def add_transaction(self, portfolio_ticker_id: int, transaction_type: str, transaction_date: datetime, shares: int, price: float, skip_duplicate: bool = True):
        epoch = datetime.fromtimestamp(0, tzutc())
        timestamp = int((datetime(transaction_date.year, transaction_date.month, transaction_date.day, tzinfo=tzutc()) - epoch).total_seconds() * 1000)

        form_data = {
            "item_id": f"{portfolio_ticker_id}",
            "type": "Buy" if transaction_type.upper() == "BUY" else "Sell",
            "date": timestamp,
            "amount": shares,
            "cost": price
        }

        if skip_duplicate:
            if self.transactions is None:
                self.transactions = self.get_existing_transactions()
            if any(form_data == transaction for transaction in self.transactions):
                logger.warning(f"Transaction {form_data} already exists. Skipping.")
                return

        if self._bearer_token is None:
            self._get_access_tokens()

        url = "https://api.simplywall.st/api/user/portfolio/transaction"
        headers = {
            "Authorization": f"Bearer {self._bearer_token}"
        }

        response = requests.post(url, form_data, headers=headers)
        if not response.status_code == 200:
            logger.warning(f"Could not add transaction for {form_data} because {response.text}.")

    @staticmethod
    def get_exchange_ticker(exchange: str, ticker: str) -> Optional[str]:
        url = f"https://legacy.simplywall.st/api/search/{exchange}:{ticker.upper()}"
        response = requests.request("GET", url)

        if response.status_code != 200:
            logger.error(f"Something went wrong when trying to get the exchange on maybe {exchange} for ticker {ticker}. Code {response.status_code}")
            return None

        tentatives = [tentative["value"] for tentative in response.json() if tentative["value"].replace(".", "") == f"{exchange}:{ticker.upper()}"]

        if len(tentatives) == 1:
            return tentatives[0]

        return None
