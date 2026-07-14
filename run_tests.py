import pytest
import sys

print(f"sys.path: {sys.path}")
sys.exit(pytest.main(["tests/"]))
