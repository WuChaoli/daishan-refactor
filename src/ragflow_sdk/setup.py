from setuptools import setup

setup(
    name="ragflow-sdk",
    version="0.1.0",
    packages=['ragflow_sdk', 'ragflow_sdk.config', 'ragflow_sdk.core', 'ragflow_sdk.http', 'ragflow_sdk.models', 'ragflow_sdk.parsers', 'ragflow_sdk.utils'],
    package_dir={'ragflow_sdk': '.'},
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "pydantic>=2.0.0",
    ],
)
