import re

PRODUCT_HREF_RE = re.compile(r".+\/product\/[^/]+")
SUMMARY_PROMO_RE = re.compile(r"Promotion Applied\: -\w+ ([\d.,]+)")
ITEM_PRICE_RE = re.compile(r"(€)([\d.,]+)")
REFUND_RE = re.compile(r"^(Return|Replacement) ")
