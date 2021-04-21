import logging
import re
from typing import Optional, List
from zlib import adler32

from bs4 import BeautifulSoup, ResultSet
from requests import Session

logger = logging.getLogger()


class WallMine:

    def __init__(self, email: str, password: str, portfolio_id: str):
        self.email = email
        self.password = password
        self.portfolio_id = portfolio_id

        self._http_session = None
        self.transactions = None

    def _get_authenticated_session(self) -> Session:
        logger.info("Getting access tokens.")
        http_session = Session()

        url = "https://wallmine.com/users/sign-in"
        response = http_session.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        authenticity_token = soup.find_all("meta", {"name": "csrf-token"})[0]["content"]

        url = "https://wallmine.com/users/sign-in"
        form_data = {
            "user[email]": self.email,
            "user[password]": self.password,
            "authenticity_token": authenticity_token,
            "user[remember_me]": "1"
        }
        response = http_session.post(url, form_data)
        if response.status_code == 200:
            logger.info("Got access keys.")
        else:
            logger.warning(f"Something went wrong when getting the access keys: {response.text}")

        return http_session

    def get_portfolio_ticker_id(self, ticker: str) -> Optional[str]:
        logger.info(f"Getting portfolio id for {ticker}.")
        if self._http_session is None:
            self._http_session = self._get_authenticated_session()

        url = f"https://wallmine.com/portfolios/{self.portfolio_id}/transactions#{ticker}"
        r = self._http_session.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        tags: List = soup.find_all("a", {"data-symbol": ticker.upper(), "title": f"Add a {ticker.upper()} transaction"})

        if len(tags) > 0:
            portfolio_ticker_id_search = re.search(r"/portfolios/\d+/item/(\d+)/transaction", tags[0].get("data-url"), re.IGNORECASE)
            if portfolio_ticker_id_search:
                return portfolio_ticker_id_search.group(1)

        return None

    def create_portfolio_ticker_id(self, exchange: str, ticker: str):
        logger.info(f"Create a portfolio ticker id for {exchange}:{ticker}.")
        if self._http_session is None:
            self._http_session = self._get_authenticated_session()

        url = f"https://wallmine.com/portfolios/{self.portfolio_id}"
        r = self._http_session.get(url)

        soup = BeautifulSoup(r.text, "html.parser")
        authenticity_token = soup.find_all("meta", {"name": "csrf-token"})[0]["content"]

        url = f"https://wallmine.com/portfolios/{self.portfolio_id}/item"
        form_data = {
            "utf8": "✓",
            "portfolio_item[symbol]": f"{exchange.upper()}:{ticker.upper()}",
            "authenticity_token": authenticity_token
        }
        response = self._http_session.post(url, form_data)

        if not response.status_code == 200 or response.text.__contains__(f"Symbol {exchange.upper()}:{ticker.upper()} not found, please try again"):
            logger.warning(f"Could not create a portfolio ticker id for {exchange}:{ticker}. "
                           f"Try adding the ticker manually in Wallmine and see if the ticker is recognized and if so, on which exchange.")

    def add_transaction(self, portfolio_ticker_id: str, transaction_type: str, date: str, shares: str, price: float, note: str, skip_duplicate: bool = True):
        if self._http_session is None:
            self._http_session = self._get_authenticated_session()

        url = f"https://wallmine.com/portfolios/{self.portfolio_id}/transactions"
        response = self._http_session.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        authenticity_token = soup.find_all("meta", {"name": "csrf-token"})[0]["content"]

        content = f"{portfolio_ticker_id}:{transaction_type}:{date}:{shares}:{price}"
        hasch = adler32(f'{content}'.encode('utf-8'))

        url = f"https://wallmine.com/portfolios/{self.portfolio_id}/item/{portfolio_ticker_id}/transaction"
        form_data = {
            "authenticity_token": authenticity_token,
            "portfolio_transaction[transaction_type]": transaction_type,
            "portfolio_transaction[date]": date,
            "portfolio_transaction[shares]": f"{shares}",
            "portfolio_transaction[price]": f"{price}",
            "portfolio_transaction[commission]": "0.00",
            "portfolio_transaction[notes]": f"{note}\n#{hasch}#",
            "utf8": "✓",
            "_method": "",
            "button": ""
        }

        if skip_duplicate:
            if self.transactions is None:
                self.transactions = self.get_existing_transactions()
            if str(hasch) in self.transactions:
                logger.warning(f"Transaction {form_data} already exists. Skipping.")
                return

        self._http_session.post(url, form_data)

    def get_existing_transactions(self) -> Optional[List[str]]:
        if self._http_session is None:
            self._http_session = self._get_authenticated_session()

        transactions = []

        logger.info("Getting hashes for existing transactions.")
        url = f"https://wallmine.com/portfolios/{self.portfolio_id}/transactions"
        response = self._http_session.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        tags: ResultSet = soup.select("tr[class^=js-transaction-] td[class=notes-column]")

        for tag in tags:
            res = re.search(r".*#(\d+)#", tag.text)
            transactions.append(res.group(1))

        return transactions
