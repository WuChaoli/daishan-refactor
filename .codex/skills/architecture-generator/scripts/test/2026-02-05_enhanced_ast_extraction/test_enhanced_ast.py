#!/usr/bin/env python3
"""
测试增强的AST提取器
验证所有功能是否正常工作
"""

import json
import sys
from pathlib import Path
from enhanced_ast_analyzer import EnhancedASTAnalyzer

def test_enhanced_ast_extraction():
    """测试增强的AST提取功能"""

    # 测试文件路径
    test_file = Path("example_sample.py")

    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False

    print("=" * 80)
    print("🚀 开始测试增强AST提取器")
    print("=" * 80)

    # 初始化分析器
    analyzer = EnhancedASTAnalyzer(test_file.parent)

    # 分析文件
    result = analyzer.analyze_file(test_file)

    # 检查是否有错误
    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
        return False

    print("\n✅ 文件分析成功!\n")

    # 测试类提取
    print("=" * 80)
    print("📦 类提取测试")
    print("=" * 80)
    print(f"提取到 {len(result['classes'])} 个类:\n")

    for cls in result['classes']:
        print(f"  类名: {cls['name']}")
        print(f"  - 位置: 第 {cls['line_number']}-{cls['end_line_number']} 行")
        print(f"  - 装饰器: {cls['decorators']}")
        print(f"  - 基类: {cls['bases']}")
        print(f"  - 方法数量: {len(cls['methods'])}")
        print(f"  - 类变量数量: {len(cls['class_variables'])}")
        print(f"  - 嵌套类数量: {len(cls['nested_classes'])}")
        print(f"  - 抽象基类: {cls['is_abstract']}")
        print(f"  - 数据类: {cls['is_dataclass']}")
        print(f"  - 异常类: {cls['is_exception']}")

        # 显示方法详情
        if cls['methods']:
            print(f"  方法列表:")
            for method in cls['methods']:
                method_type = []
                if method['is_static_method']:
                    method_type.append("@staticmethod")
                if method['is_class_method']:
                    method_type.append("@classmethod")
                if method['is_property']:
                    method_type.append("@property")
                if method['is_async']:
                    method_type.append("async")

                method_type_str = f" ({', '.join(method_type)})" if method_type else ""
                print(f"    - {method['name']}{method_type_str}")
                params = [p['name'] for p in method['parameters']]
                print(f"      参数: {', '.join(params)}")
                print(f"      返回类型: {method['return_type'] or 'None'}")

        print()

    # 测试函数提取
    print("=" * 80)
    print("⚙️ 函数提取测试")
    print("=" * 80)
    print(f"提取到 {len(result['functions'])} 个函数:\n")

    for func in result['functions']:
        print(f"  函数名: {func['name']}")
        print(f"  - 位置: 第 {func['line_number']}-{func['end_line_number']} 行")
        print(f"  - 装饰器: {func['decorators']}")

        # 参数信息
        params_info = []
        for p in func['parameters']:
            param_str = p['name']
            if p['type_annotation']:
                param_str += f": {p['type_annotation']}"
            if p['default_value']:
                param_str += f" = {p['default_value']}"
            params_info.append(param_str)

        print(f"  - 参数: {', '.join(params_info)}")
        print(f"  - 返回类型: {func['return_type'] or 'None'}")

        # 函数类型
        func_type = []
        if func['is_async']:
            func_type.append("async")
        if func['is_generator']:
            func_type.append("generator")
        if func['is_async_generator']:
            func_type.append("async generator")
        if func['is_static_method']:
            func_type.append("@staticmethod")
        if func['is_class_method']:
            func_type.append("@classmethod")
        if func['is_property']:
            func_type.append("@property")

        if func_type:
            print(f"  - 类型: {', '.join(func_type)}")

        # await 表达式计数
        if func['await_count'] > 0:
            print(f"  - await 表达式: {func['await_count']} 个")

        # 嵌套函数
        if func['nested_functions']:
            print(f"  - 嵌套函数: {[f['name'] for f in func['nested_functions']]}")

        print()

    # 测试依赖提取
    print("=" * 80)
    print("🔗 依赖提取测试")
    print("=" * 80)

    dependencies = result['dependencies']
    print(f"导入语句: {len(dependencies.get('imports', []))} 个")
    print(f"函数调用: {len(dependencies.get('calls', []))} 个")
    print(f"类实例化: {len(dependencies.get('instantiations', []))} 个")
    print(f"类型注解: {len(dependencies.get('type_hints', []))} 个\n")

    if dependencies.get('imports'):
        print("导入依赖:")
        for dep in dependencies['imports']:
            external = "外部" if dep['is_external'] else "内部"
            print(f"  - {dep['name']} ({external})")
        print()

    # 测试变量提取
    print("=" * 80)
    print("📝 变量提取测试")
    print("=" * 80)

    variables = result['variables']
    total_vars = sum(len(vars) for vars in variables.values())
    print(f"提取到 {total_vars} 个变量\n")

    if variables.get('global'):
        print(f"全局变量 ({len(variables['global'])} 个):")
        for var in variables['global']:
            type_str = f": {var['type_annotation']}" if var['type_annotation'] else ""
            value_str = f" = {var['value']}" if var['value'] else ""
            print(f"  - {var['name']}{type_str}{value_str}")
        print()

    # 测试模式提取
    print("=" * 80)
    print("🎯 模式提取测试")
    print("=" * 80)

    patterns = result['patterns']
    print(f"异常处理器: {len(patterns.get('exception_handlers', []))} 个")
    print(f"上下文管理器: {len(patterns.get('context_managers', []))} 个")
    print(f"Lambda 函数: {len(patterns.get('lambdas', []))} 个\n")

    if patterns.get('exception_handlers'):
        print("异常处理器:")
        for handler in patterns['exception_handlers']:
            print(f"  - 第 {handler['line_number']} 行: {', '.join(handler['exception_types'])}")
        print()

    if patterns.get('context_managers'):
        print("上下文管理器:")
        for ctx in patterns['context_managers']:
            vars_str = ', '.join(ctx['variable_names']) if ctx['variable_names'] else '无'
            print(f"  - 第 {ctx['line_number']} 行: {ctx['context_expr']} -> [{vars_str}]")
        print()

    if patterns.get('lambdas'):
        print("Lambda 函数:")
        for lam in patterns['lambdas']:
            print(f"  - 第 {lam['line_number']} 行: lambda {lam['arguments']}: {lam['body']}")
        print()

    # 统计摘要
    print("=" * 80)
    print("📊 统计摘要")
    print("=" * 80)
    print(f"✅ 总计提取:")
    print(f"  - 类: {len(result['classes'])} 个")
    print(f"  - 函数: {len(result['functions'])} 个")
    print(f"  - 导入: {len(dependencies.get('imports', []))} 个")
    print(f"  - 变量: {total_vars} 个")
    print(f"  - 异常处理器: {len(patterns.get('exception_handlers', []))} 个")
    print(f"  - 上下文管理器: {len(patterns.get('context_managers', []))} 个")
    print(f"  - Lambda 函数: {len(patterns.get('lambdas', []))} 个")
    print()

    # 功能验证检查
    print("=" * 80)
    print("✔️ 功能验证")
    print("=" * 80)

    checks = []

    # 检查抽象基类检测
    abstract_classes = [c for c in result['classes'] if c['is_abstract']]
    checks.append(("抽象基类检测", len(abstract_classes) > 0, len(abstract_classes)))

    # 检查数据类检测
    dataclasses = [c for c in result['classes'] if c['is_dataclass']]
    checks.append(("数据类检测", len(dataclasses) > 0, len(dataclasses)))

    # 检查异步函数检测
    async_funcs = [f for f in result['functions'] if f['is_async']]
    checks.append(("异步函数检测", len(async_funcs) > 0, len(async_funcs)))

    # 检查生成器检测
    generators = [f for f in result['functions'] if f['is_generator'] or f['is_async_generator']]
    checks.append(("生成器检测", len(generators) > 0, len(generators)))

    # 检查方法装饰器检测
    decorated_methods = []
    for cls in result['classes']:
        for method in cls['methods']:
            if method['is_static_method'] or method['is_class_method'] or method['is_property']:
                decorated_methods.append(method)
    checks.append(("方法装饰器检测", len(decorated_methods) > 0, len(decorated_methods)))

    # 检查嵌套函数检测
    nested_funcs = [f for f in result['functions'] if f['nested_functions']]
    checks.append(("嵌套函数检测", len(nested_funcs) > 0, len(nested_funcs)))

    # 检查异常处理检测
    checks.append(("异常处理检测", len(patterns.get('exception_handlers', [])) > 0,
                  len(patterns.get('exception_handlers', []))))

    # 检查上下文管理器检测
    checks.append(("上下文管理器检测", len(patterns.get('context_managers', [])) > 0,
                  len(patterns.get('context_managers', []))))

    # 检查 Lambda 检测
    checks.append(("Lambda 函数检测", len(patterns.get('lambdas', [])) > 0,
                  len(patterns.get('lambdas', []))))

    # 打印检查结果
    all_passed = True
    for check_name, passed, count in checks:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {check_name} (发现 {count} 个)")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 所有功能验证通过!")
    else:
        print("⚠️ 部分功能验证失败")

    print("=" * 80)

    return all_passed

if __name__ == "__main__":
    success = test_enhanced_ast_extraction()
    sys.exit(0 if success else 1)
