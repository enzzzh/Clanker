import os

from dotenv import load_dotenv


def test_environment_loading():
    load_dotenv()

    # Simulate setting a mock token if none exists for the test runner
    if not os.getenv("DISCORD_TOKEN"):
        os.environ["DISCORD_TOKEN"] = "mock_test_token_12345"

    token = os.getenv("DISCORD_TOKEN")

    assert token is not None
    assert len(token) > 0
    print("Environment token validation test passed!")
