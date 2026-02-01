import re

class IntelExtractor:
    UPI_REGEX = r"[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}"
    URL_REGEX = r"https?://[^\s]+"

    def extract(self, text):
        return {
            "upi_ids": re.findall(self.UPI_REGEX, text),
            "links": re.findall(self.URL_REGEX, text),
            "bank_accounts": []  # extend later
        }
