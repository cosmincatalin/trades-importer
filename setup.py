from setuptools import setup

setup(
    name="trades-importer",
    version="1.0.1",
    author="Cosmin Catalin Sanda",
    author_email="cosmincatalin@gmail.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    packages=[
        "trades_importer"
    ],
    install_requires=["requests==2.25.1"]
)