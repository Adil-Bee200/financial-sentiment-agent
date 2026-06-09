import logging
from typing import List

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, PortfolioTickers

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def create_portfolio(self, portfolio: Portfolio) -> Portfolio:
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def get_portfolio(self, portfolio_id: int) -> Portfolio:
        portfolio = self.db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
        if not portfolio:
            raise LookupError("Portfolio not found")
        return portfolio

    def update_portfolio(self, portfolio_id: int, name: str) -> Portfolio:
        existing = self.get_portfolio(portfolio_id)
        stripped = name.strip()
        if not stripped:
            raise ValueError("Portfolio name cannot be empty")
        existing.name = stripped
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete_portfolio(self, portfolio_id: int) -> None:
        self.db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).delete()
        self.db.commit()

    def get_all_portfolios(self) -> List[Portfolio]:
        return self.db.query(Portfolio).all()

    def get_portfolio_by_user_id(self, user_id: int) -> List[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    def add_ticker_to_portfolio(self, portfolio_id: int, ticker: str) -> PortfolioTickers:
        existing_ticker = self.db.query(PortfolioTickers).filter(
            PortfolioTickers.portfolio_id == portfolio_id,
            PortfolioTickers.ticker == ticker,
        ).first()
        if existing_ticker:
            raise ValueError("Ticker already exists in portfolio")

        new_ticker = PortfolioTickers(portfolio_id=portfolio_id, ticker=ticker)
        self.db.add(new_ticker)
        self.db.commit()
        self.db.refresh(new_ticker)
        return new_ticker

    def remove_ticker_from_portfolio(self, portfolio_id: int, ticker: str) -> None:
        existing_ticker = self.get_ticker_from_portfolio(portfolio_id, ticker)
        self.db.delete(existing_ticker)
        self.db.commit()

    def get_all_tickers_from_portfolio(self, portfolio_id: int) -> List[PortfolioTickers]:
        return self.db.query(PortfolioTickers).filter(
            PortfolioTickers.portfolio_id == portfolio_id
        ).all()

    def get_ticker_from_portfolio(self, portfolio_id: int, ticker: str) -> PortfolioTickers:
        existing_ticker = (
            self.db.query(PortfolioTickers)
            .filter(PortfolioTickers.portfolio_id == portfolio_id)
            .filter(PortfolioTickers.ticker == ticker)
            .first()
        )
        if not existing_ticker:
            raise LookupError("Ticker not found in portfolio")
        return existing_ticker

    def get_all_tracked_tickers(self) -> List[str]:
        tickers_result = self.db.query(PortfolioTickers.ticker).distinct().all()
        return [ticker[0] for ticker in tickers_result]

    def get_tracked_tickers_by_user(self, user_id: int) -> List[str]:
        tickers_result = (
            self.db.query(PortfolioTickers.ticker)
            .join(Portfolio, PortfolioTickers.portfolio_id == Portfolio.portfolio_id)
            .filter(Portfolio.user_id == user_id)
            .distinct()
            .all()
        )
        return [ticker[0] for ticker in tickers_result]
