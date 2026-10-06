from vendoriq.scraper import normalize_url, same_domain, should_skip_url


def test_normalize_preserves_business_query_and_removes_fragment():
    url = normalize_url(
        "/products-detail.php?id=5&utm_source=newsletter#top",
        "https://www.acme.com/",
    )
    assert url == "https://www.acme.com/products-detail.php?id=5"


def test_same_domain_ignores_www():
    assert same_domain("https://www.acme.com/products", "https://acme.com")


def test_skip_non_web_links_and_assets():
    assert should_skip_url("mailto:sales@acme.com")
    assert should_skip_url("https://acme.com/logo.png?version=2")
