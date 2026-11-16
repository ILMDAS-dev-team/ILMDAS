def test_catalogue_package_imports():
    import apps.catalogue as app

    assert app.__name__ == "apps.catalogue"
