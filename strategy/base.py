from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    @abstractmethod
    def generate_signal(self, price_history: pd.Series) -> str:
        pass
