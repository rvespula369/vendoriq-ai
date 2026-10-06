from vendoriq.scraper import PageDocument
from vendoriq.service import _unique_pages


def test_unique_pages_deduplicates_canonical_urls():
    pages = [
        PageDocument("https://acme.com/products?id=5", "A", "one"),
        PageDocument("https://acme.com/products?id=5#top", "B", "two"),
        PageDocument("https://acme.com/products?id=6", "C", "three"),
    ]
    result = _unique_pages(pages)
    assert [page.url for page in result] == [
        "https://acme.com/products?id=5",
        "https://acme.com/products?id=6",
    ]
