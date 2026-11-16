def test_circulation_package_imports():
    import apps.circulation as app

    assert app.__name__ == "apps.circulation"
