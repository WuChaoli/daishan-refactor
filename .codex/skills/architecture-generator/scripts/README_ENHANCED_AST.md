# Enhanced Python AST Extraction

## 概述

这个模块提供了增强的 Python AST（抽象语法树）提取功能，用于从 Python 代码中提取详细的类、函数和依赖关系信息。

## 功能特性

### 1. 类提取 (ClassExtractor)
- ✅ 类名和装饰器
- ✅ 基类列表
- ✅ 所有方法（包括参数、返回类型、装饰器）
- ✅ 类变量
- ✅ 嵌套类
- ✅ 文档字符串
- ✅ 特殊类类型检测：
  - 抽象基类 (ABC)
  - 数据类 (dataclass)
  - 异常类 (Exception)

### 2. 函数提取 (FunctionExtractor)
- ✅ 函数名和装饰器
- ✅ 完整参数信息：
  - 位置-only 参数
  - 常规参数
  - *args
  - 关键字-only 参数
  - **kwargs
- ✅ 类型注解
- ✅ 默认值
- ✅ 返回类型
- ✅ 文档字符串
- ✅ 特殊函数类型检测：
  - 异步函数
  - 生成器 (yield)
  - 异步生成器 (async yield)
  - 静态方法
  - 类方法
  - 属性
- ✅ 嵌套函数
- ✅ await 表达式计数

### 3. 依赖提取 (DependencyExtractor)
- ✅ 导入语句 (import)
- ✅ from 导入 (from ... import)
- ✅ 函数调用依赖
- ✅ 类实例化依赖
- ✅ 类型注解依赖
- ✅ 内部 vs 外部依赖区分

### 4. 变量提取 (VariableExtractor)
- ✅ 全局变量
- ✅ 类变量
- ✅ 类型注解
- ✅ 初始值

### 5. 模式提取 (PatternExtractor)
- ✅ 异常处理器
- ✅ 上下文管理器 (with 语句)
- ✅ Lambda 函数

### 6. 调用图构建 (CallGraphBuilder)
- ✅ 函数调用关系跟踪
- ✅ 数据库存储
- ✅ 调用者/被调用者查询
- ✅ 传递闭包计算

## 文件结构

```
ast_extractors/
├── __init__.py                    # 包初始化
├── base_extractor.py              # 基础提取器类
├── class_extractor.py             # 类提取器
├── function_extractor.py          # 函数提取器
├── dependency_extractor.py        # 依赖提取器
├── variable_extractor.py          # 变量提取器
├── pattern_extractor.py           # 模式提取器
├── call_graph_builder.py          # 调用图构建器
└── enhanced_ast_analyzer.py       # 主分析器
```

## 使用方法

### 基本使用

```python
from pathlib import Path
from enhanced_ast_analyzer import EnhancedASTAnalyzer

# 初始化分析器
analyzer = EnhancedASTAnalyzer(
    project_path=Path("/path/to/project")
)

# 分析单个文件
result = analyzer.analyze_file(Path("src/main.py"))

# 访问提取的信息
for class_info in result['classes']:
    print(f"Class: {class_info['name']}")
    print(f"  Decorators: {class_info['decorators']}")
    print(f"  Base classes: {class_info['bases']}")
    print(f"  Methods: {[m['name'] for m in class_info['methods']]}")

for func_info in result['functions']:
    print(f"Function: {func_info['name']}")
    print(f"  Parameters: {[p['name'] for p in func_info['parameters']]}")
    print(f"  Return type: {func_info['return_type']}")

for dep in result['dependencies']['imports']:
    print(f"Import: {dep['name']}")
```

### 命令行使用

```bash
# 分析单个文件
python enhanced_ast_analyzer.py /path/to/file.py

# 构建符号索引
python build_symbol_index.py /path/to/project

# 分析依赖关系
python analyze_dependencies.py /path/to/project
```

## 示例输出

### 类信息

```json
{
  "name": "Rectangle",
  "file_path": "example.py",
  "line_number": 45,
  "end_line_number": 78,
  "decorators": [],
  "bases": [],
  "methods": [
    {
      "name": "__init__",
      "parameters": [
        {
          "name": "self",
          "type_annotation": null,
          "default_value": null,
          "is_positional_only": false,
          "is_keyword_only": false,
          "is_var_positional": false,
          "is_var_keyword": false
        },
        {
          "name": "width",
          "type_annotation": "float",
          "default_value": null,
          "is_positional_only": false,
          "is_keyword_only": false,
          "is_var_positional": false,
          "is_var_keyword": false
        }
      ],
      "return_type": null,
      "is_async": false,
      "is_method": true,
      "is_static_method": false,
      "is_class_method": false,
      "is_property": false,
      "is_generator": false
    },
    {
      "name": "area",
      "parameters": [
        {
          "name": "self",
          "type_annotation": null,
          "default_value": null,
          "is_positional_only": false,
          "is_keyword_only": false,
          "is_var_positional": false,
          "is_var_keyword": false
        }
      ],
      "return_type": "float",
      "docstring": "计算面积",
      "is_async": false,
      "is_method": true,
      "is_static_method": false,
      "is_class_method": false,
      "is_property": false,
      "is_generator": false
    }
  ],
  "class_variables": [],
  "nested_classes": [],
  "docstring": "矩形",
  "is_abstract": false,
  "is_dataclass": false,
  "is_exception": false
}
```

### 函数信息

```json
{
  "name": "fetch_data",
  "file_path": "example.py",
  "line_number": 115,
  "end_line_number": 119,
  "decorators": [],
  "parameters": [
    {
      "name": "url",
      "type_annotation": "str",
      "default_value": null,
      "is_positional_only": false,
      "is_keyword_only": false,
      "is_var_positional": false,
      "is_var_keyword": false
    }
  ],
  "return_type": "Dict",
  "docstring": "获取数据",
  "is_async": true,
  "is_method": false,
  "is_static_method": false,
  "is_class_method": false,
  "is_property": false,
  "is_generator": false,
  "is_async_generator": false,
  "nested_functions": [],
  "await_count": 1
}
```

### 依赖信息

```json
{
  "imports": [
    {
      "name": "abc",
      "dep_type": "import",
      "line_number": 4,
      "is_external": true,
      "module_path": "abc"
    },
    {
      "name": "asyncio",
      "dep_type": "import",
      "line_number": 5,
      "is_external": true,
      "module_path": "asyncio"
    }
  ],
  "calls": [],
  "instantiations": [],
  "type_hints": [
    {
      "name": "Optional",
      "dep_type": "type_hint",
      "line_number": 6,
      "is_external": true,
      "module_path": null
    }
  ]
}
```

## 集成到现有代码

增强的 AST 提取器已集成到 `build_symbol_index.py` 和 `analyze_dependencies.py` 中：

1. **build_symbol_index.py**: 使用增强提取器收集更详细的符号信息
2. **analyze_dependencies.py**: 使用增强提取器收集更完整的依赖关系

如果增强提取器失败，系统会自动回退到基本实现。

## 测试

查看 `example_sample.py` 文件以了解各种 Python 特性的示例。

运行以下命令测试提取器：

```bash
# 分析示例文件
python enhanced_ast_analyzer.py .codex/skills/architecture-generator/scripts/example_sample.py
```

## 性能考虑

- AST 树在单文件分析期间会被缓存
- 尽可能重用提取器实例
- 谨慎使用 `ast.unparse()`（它很昂贵）
- 使用事务批量操作数据库

## 限制

- 目前仅支持 Python 代码
- 其他语言（JavaScript/TypeScript）仍使用正则表达式
- 需要 Python 3.8+ 以支持某些特性（如位置-only 参数）

## 未来改进

- [ ] 支持更多 Python 版本
- [ ] 添加 JavaScript/TypeScript AST 支持
- [ ] 改进外部依赖检测
- [ ] 添加更多模式识别
- [ ] 性能优化

## 相关文档

- [Python AST 文档](https://docs.python.org/3/library/ast.html)
- [Green Tree Snakes AST 指南](https://greentreesnakes.readthedocs.io/)
- [build_symbol_index.py](build_symbol_index.md)
- [analyze_dependencies.py](analyze_dependencies.md)
