def test_archive_package_imports():
    import apps.archive as app

    assert app.__name__ == "apps.archive"
