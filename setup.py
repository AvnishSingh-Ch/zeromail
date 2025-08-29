#!/usr/bin/env python3
"""
Setup script for Gmail IMAP Cleaner
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gmail-imap-cleaner",
    version="2.0.0",
    author="Zoro",
    description="Advanced Gmail IMAP email management and cleanup tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/gmail-imap-cleaner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Email",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest>=6.2.0", "black>=21.0.0", "flake8>=4.0.0"],
        "analytics": ["matplotlib>=3.5.0", "plotly>=5.0.0", "pandas>=1.3.0"],
        "gui": ["tkinter-modern>=1.0.0", "PyQt6>=6.0.0"],
        "web": ["flask>=2.0.0", "fastapi>=0.70.0", "uvicorn>=0.15.0"],
    },
    entry_points={
        "console_scripts": [
            "gmail-cleaner=main:main",
            "gmail-session=gmail_session:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
