from setuptools import setup

setup(
    name="dify-sdk",
    version="1.0.0",
    packages=['dify_sdk', 'dify_sdk.core', 'dify_sdk.http', 'dify_sdk.models', 'dify_sdk.parsers'],
    package_dir={'dify_sdk': '.'},
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.1",
    ],
)
