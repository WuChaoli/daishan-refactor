from setuptools import setup, find_packages

setup(
    name="DaiShanSQL",          # 包名（外部导入时用这个名字）
    version="0.2.0",            # 版本号
    packages=find_packages(),   # 自动识别所有包（无需手动列）
    python_requires=">=3.8",    # 兼容的Python版本（根据你的项目调整）
)