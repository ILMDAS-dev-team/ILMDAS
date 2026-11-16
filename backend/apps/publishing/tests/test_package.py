def test_publishing_package_imports():
    import apps.publishing as app

    assert app.__name__ == "apps.publishing"
