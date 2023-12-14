import locale
from decimal import Decimal
from blockchainetl.jobs.exporters.converters import SimpleItemConverter

locale.setlocale(locale.LC_ALL, "")

CURRENCY_KEYS = ("usd", "amount")
CURRENCY_TYPS = (int, float, Decimal)


class CurrencyItemConverter(SimpleItemConverter):
    def convert_field(self, key, value):
        suffix = key.split("_")[-1]
        if suffix in CURRENCY_KEYS and isinstance(value, CURRENCY_TYPS):
            return locale.currency(value, grouping=True, symbol=suffix == "usd")
        return value
