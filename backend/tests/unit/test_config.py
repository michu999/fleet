import pytest
from pydantic import ValidationError
from app.core.config import Settings

class TestSecretKeyValidation:
    def test_empty_secret_key_raises_error(self):
        with pytest.raises(ValidationError):
            Settings(SECRET_KEY="", ENVIRONMENT="production", _env_file=None)

    def test_short_secret_key_raises_error(self):
        with pytest.raises(ValidationError):
            Settings(SECRET_KEY="short", ENVIRONMENT="production", _env_file=None)

