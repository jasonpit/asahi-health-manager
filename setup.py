#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="asahi-system-healer",
    version="1.0.0",
    author="Asahi System Healer Team",
    author_email="info@example.com",
    description="Advanced AI-powered system health management for Asahi Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/asahi-health-manager",
    project_urls={
        "Bug Reports": "https://github.com/your-repo/asahi-health-manager/issues",
        "Source": "https://github.com/your-repo/asahi-health-manager",
        "Documentation": "https://github.com/your-repo/asahi-health-manager/wiki",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "asahi-healer=asahi_healer:main",
            "asahi-system-healer=asahi_healer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.md"],
    },
    zip_safe=False,
    keywords="asahi linux apple silicon system health monitoring automation ai",
    platforms=["Linux"],
)