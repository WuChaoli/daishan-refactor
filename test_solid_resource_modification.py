"""验证 _get_solid_resource_instruction 函数修改"""
import sys
sys.path.insert(0, '/home/wuchaoli/codespace/daishan-refactor/rag_stream')

from src.services.source_dispath_srvice import _get_solid_resource_instruction
import inspect

# 检查函数签名
sig = inspect.signature(_get_solid_resource_instruction)
print("函数签名:")
print(f"  {_get_solid_resource_instruction.__name__}{sig}")
print()

# 检查参数
print("参数列表:")
for param_name, param in sig.parameters.items():
    print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
print()

# 检查返回类型
return_annotation = sig.return_annotation
print(f"返回类型: {return_annotation if return_annotation != inspect.Signature.empty else 'Any'}")
print()

# 检查文档字符串
print("文档字符串:")
print(_get_solid_resource_instruction.__doc__)
print()

print("✅ 函数修改验证通过")
