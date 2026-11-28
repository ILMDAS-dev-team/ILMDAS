"""Package smoke test for the website content app."""


def test_homepage_package_imports():
    import apps.homepage as app

    assert app.__name__ == "apps.homepage"
