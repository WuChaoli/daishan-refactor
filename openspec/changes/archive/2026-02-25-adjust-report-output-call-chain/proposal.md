## Why

当前 report 输出缺少函数之间的调用关系，排查问题时难以快速定位调用路径和故障传播链。现在需要在 report 中直接呈现调用链，以提升可观测性与定位效率。

## What Changes

- 在 report 输出中新增“函数调用链”能力，展示调用顺序与父子关系。
- 统一调用链输出结构，明确每一层调用节点的关键信息（函数标识、层级、时序/结果状态）。
- 保持现有 report 主要内容可用，调用链作为增强信息并入输出。

## Capabilities

### New Capabilities

- `report-function-call-chain`: report 必须能够输出函数调用链，包含调用层级关系和执行顺序，用于定位执行路径与异常传播。

### Modified Capabilities

- （无）

## Impact

- 受影响代码：report 生成相关模块、函数调用采集/聚合逻辑、report 输出组装逻辑。
- 受影响测试：report 输出相关单测与集成测试需要覆盖调用链场景。
- 兼容性影响：report 输出结构新增调用链信息，下游若对输出结构做严格匹配，可能需要同步适配。
