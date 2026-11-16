def test_accounts_package_imports():
    import apps.accounts as app

    assert app.__name__ == "apps.accounts"
