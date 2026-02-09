#!/usr/bin/env python3
"""
示例文件：展示增强的 AST 提取功能

这个文件包含各种 Python 特性，用于测试 AST 提取器。
"""

import abc
import asyncio
from dataclasses import dataclass
from typing import Optional, List, Dict


# ============================================================================
# 类定义示例
# ============================================================================

# 抽象基类
class Shape(abc.ABC):
    """抽象基类"""

    @abc.abstractmethod
    def area(self) -> float:
        """计算面积"""
        pass

    @abc.abstractmethod
    def perimeter(self) -> float:
        """计算周长"""
        pass


# 数据类
@dataclass
class Point:
    """2D 点"""
    x: float
    y: float


# 带装饰器的类
class Rectangle:
    """矩形"""

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def area(self) -> float:
        """计算面积"""
        return self.width * self.height

    @property
    def size(self) -> float:
        """获取大小"""
        return self.area()

    @classmethod
    def from_dimensions(cls, width: float, height: float) -> 'Rectangle':
        """从尺寸创建"""
        return cls(width, height)

    @staticmethod
    def is_valid(width: float, height: float) -> bool:
        """检查尺寸是否有效"""
        return width > 0 and height > 0


# 异常类
class ValidationError(Exception):
    """自定义验证错误"""
    pass


# 嵌套类
class Container:
    """容器"""

    class Inner:
        """内部类"""
        pass


# ============================================================================
# 函数定义示例
# ============================================================================

# 简单函数
def add(a: int, b: int) -> int:
    """加法"""
    return a + b


# 带默认值的函数
def greet(name: str, greeting: str = "Hello") -> str:
    """问候"""
    return f"{greeting}, {name}!"


# 异步函数
async def fetch_data(url: str) -> Dict:
    """获取数据"""
    response = await asyncio.get(url)
    return response


# 异步生成器
async def async_range(n: int):
    """异步范围生成器"""
    for i in range(n):
        yield i
        await asyncio.sleep(0.1)


# 普通生成器
def fibonacci(n: int):
    """斐波那契生成器"""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


# 带关键字-only 参数的函数
def process_data(
    data: List[int],
    *,
    normalize: bool = True,
    sort: bool = False
) -> List[int]:
    """处理数据"""
    result = data.copy()
    if normalize:
        result = [x / max(result) for x in result]
    if sort:
        result.sort()
    return result


# 带位置-only 参数的函数 (Python 3.8+)
def divide(a: float, b: float, /) -> float:
    """除法"""
    return a / b


# 嵌套函数
def outer_function(x: int) -> int:
    """外部函数"""

    def inner(y: int) -> int:
        """内部函数"""
        return y * 2

    return inner(x) + 1


# ============================================================================
# 异常处理示例
# ============================================================================

def risky_operation(x: int) -> int:
    """带异常处理的函数"""
    try:
        return 100 // x
    except ZeroDivisionError as e:
        print(f"Error: {e}")
        return 0
    except (ValueError, TypeError) as e:
        print(f"Type error: {e}")
        return -1
    except:
        print("Unknown error")
        return -2
    finally:
        print("Cleanup")


# ============================================================================
# 上下文管理器示例
# ============================================================================

def read_file_safely(path: str) -> str:
    """安全读取文件"""
    with open(path, 'r') as f:
        return f.read()


def multiple_contexts():
    """多个上下文管理器"""
    with open('input.txt', 'r') as infile, \
         open('output.txt', 'w') as outfile:
        data = infile.read()
        outfile.write(data.upper())


# ============================================================================
# Lambda 函数示例
# ============================================================================

def lambda_examples():
    """Lambda 示例"""
    numbers = [1, 2, 3, 4, 5]

    # Map with lambda
    doubled = list(map(lambda x: x * 2, numbers))

    # Filter with lambda
    evens = list(filter(lambda x: x % 2 == 0, numbers))

    # Sort with lambda
    words = ['apple', 'banana', 'cherry']
    sorted_words = sorted(words, key=lambda w: len(w))

    return doubled, evens, sorted_words


# ============================================================================
# 全局变量示例
# ============================================================================

# 全局常量
MAX_SIZE: int = 100
DEFAULT_TIMEOUT: float = 30.0

# 全局配置
config: Dict[str, str] = {
    'host': 'localhost',
    'port': '8080'
}


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    # 创建点
    point = Point(10.0, 20.0)
    print(f"Point: ({point.x}, {point.y})")

    # 创建矩形
    rect = Rectangle(5.0, 3.0)
    print(f"Area: {rect.area()}")
    print(f"Size: {rect.size}")

    # 测试函数
    result = add(5, 3)
    print(f"5 + 3 = {result}")

    # 测试异步函数
    async def main():
        data = await fetch_data("https://example.com")
        print(f"Data: {data}")

    # 运行异步函数
    asyncio.run(main())
