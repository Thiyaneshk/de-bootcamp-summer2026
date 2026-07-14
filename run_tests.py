import sys
import pytest

print(f"sys.path: {sys.path}")
sys.exit(pytest.main(["tests/"]))
