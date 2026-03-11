from setuptools import find_packages, setup


setup(
    name="DaiShanSQL",
    version="0.2.1",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "python-dateutil>=2.8.2",
    ],
)
