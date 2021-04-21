from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="trades-importer",
    version="1.0.2",
    author="Cosmin Catalin Sanda",
    author_email="cosmincatalin@gmail.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    packages=[
        "trades_importer"
    ],
    description="Connector library for importing stock trading information to various services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["requests>=2", "beautifulsoup4>=4"]
)