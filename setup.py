#!/usr/bin/env python3
"""
Setup script for Kalshi Trading Solution.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kalshihub",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python-based trading solution for the Kalshi prediction market platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.13",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "kalshihub=src.main:main",
        ],
    },
)
