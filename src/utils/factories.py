import factory.fuzzy
from moneyed import Money


class FuzzyMoney(factory.fuzzy.FuzzyDecimal):
    def fuzz(self):
        return Money(super().fuzz(), 'SEK')
