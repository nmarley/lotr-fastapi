def pytest_addoption(parser):
    """Add integration test option to pytest"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external API access",
    )
