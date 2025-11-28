from setuptools import setup, find_packages

setup(
    name="shark-event",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        # Add other dependencies here
    ],
    entry_points={
        "console_scripts": [
            "shark-event=app.interfaces.cli.cli:cli",
        ],
    },
)
