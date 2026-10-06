from vendoriq.scraper import DiscoveredLink
from vendoriq.selector import select_relevant_links


def test_product_and_quality_pages_rank_above_privacy():
    links = [
        DiscoveredLink("https://acme.com/privacy", "Privacy Policy"),
        DiscoveredLink("https://acme.com/products", "Products"),
        DiscoveredLink("https://acme.com/quality/certifications", "Quality Certifications"),
        DiscoveredLink("https://acme.com/blog/post", "Latest Blog"),
    ]
    selected = select_relevant_links(links, limit=3)
    urls = [item.url for item in selected]
    assert "https://acme.com/products" in urls
    assert "https://acme.com/quality/certifications" in urls
    assert "https://acme.com/privacy" not in urls
