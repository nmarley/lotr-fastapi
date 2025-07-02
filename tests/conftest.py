def pytest_addoption(parser):
    """Add integration test option to pytest"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external API access",
    )


def pytest_configure(config):
    """Register custom pytest marks"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test requiring external API access",
    )
