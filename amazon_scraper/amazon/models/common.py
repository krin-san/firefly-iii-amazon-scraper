import re

PRODUCT_HREF_RE = re.compile(r".+\/product\/[^/]+")
SUMMARY_PROMO_RE = re.compile(r"Promotion Applied\: -\w+ ([\d.,]+)")
