"""Compatibility import for earlier code that used ``merge.generate``."""

from generator import generate


if __name__ == "__main__":
    generate(1000000, 1000000, 1000000, 10, 2, 8)
