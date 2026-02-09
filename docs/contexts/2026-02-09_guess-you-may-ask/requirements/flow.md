# 猜你想问功能 - 流程图

## 1. 整体流程图

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端
    participant API as /api/guess-questions
    participant IntentService as IntentService
    participant PostProcessor as 后处理函数

    User->>Frontend: 输入问题
    Frontend->>API: POST /api/guess-questions<br/>{question: "用户问题"}

    API->>IntentService: process_query(question, user_id)
    IntentService-->>API: 返回意图识别结果<br/>{type, results, similarity, database}

    API->>PostProcessor: 根据type选择后处理函数

    alt type == 1 (类别1)
        PostProcessor->>PostProcessor: 返回固定的3个问题
    else type == 2 (类别2)
        PostProcessor->>PostProcessor: 提取results[1:4]的question字段
    else type == 0 或其他
        PostProcessor->>PostProcessor: 返回空列表
    end

    PostProcessor-->>API: 推荐问题列表
    API-->>Frontend: {code: 0, message: "成功", data: [...]}
    Frontend-->>User: 展示推荐问题
```

## 2. 意图识别流程

```mermaid
flowchart TD
    Start([开始]) --> Input[接收用户问题]
    Input --> CallIntent[调用IntentService.process_query]
    CallIntent --> CheckError{调用成功?}

    CheckError -->|失败| ErrorHandle[错误处理]
    ErrorHandle --> ReturnError[返回错误响应]
    ReturnError --> End([结束])

    CheckError -->|成功| ParseResult[解析意图识别结果]
    ParseResult --> GetType[获取type字段]
    GetType --> CheckType{判断type类型}

    CheckType -->|type == 1| FixedQuestions[返回固定的3个问题]
    CheckType -->|type == 2| ExtractQuestions[提取results[1:4]的question]
    CheckType -->|其他| EmptyList[返回空列表]

    FixedQuestions --> FormatResponse[格式化响应]
    ExtractQuestions --> FormatResponse
    EmptyList --> FormatResponse

    FormatResponse --> ReturnSuccess[返回成功响应]
    ReturnSuccess --> End
```

## 3. 类别2问题提取流程

```mermaid
flowchart TD
    Start([开始]) --> GetResults[获取results列表]
    GetResults --> CheckLength{results长度}

    CheckLength -->|长度 < 2| ReturnEmpty[返回空列表]
    CheckLength -->|长度 >= 2| ExtractRange[提取索引1-3的元素]

    ExtractRange --> CheckExtracted{提取的元素数量}
    CheckExtracted -->|1个| Format1[格式化1个问题]
    CheckExtracted -->|2个| Format2[格式化2个问题]
    CheckExtracted -->|3个| Format3[格式化3个问题]

    Format1 --> BuildResponse[构建响应列表]
    Format2 --> BuildResponse
    Format3 --> BuildResponse
    ReturnEmpty --> BuildResponse

    BuildResponse --> End([结束])
```

## 4. 错误处理流程

```mermaid
flowchart TD
    Start([开始]) --> TryCall[尝试调用IntentService]
    TryCall --> CheckException{是否抛出异常?}

    CheckException -->|无异常| ParseResult[解析结果]
    CheckException -->|有异常| LogError[记录错误日志]

    LogError --> CheckErrorType{异常类型}
    CheckErrorType -->|网络异常| NetworkError[返回"意图识别服务不可用"]
    CheckErrorType -->|数据格式异常| FormatError[返回"数据格式错误"]
    CheckErrorType -->|其他异常| GeneralError[返回"系统异常"]

    NetworkError --> BuildErrorResponse[构建错误响应]
    FormatError --> BuildErrorResponse
    GeneralError --> BuildErrorResponse

    BuildErrorResponse --> ReturnError[返回错误响应<br/>{code: 1, message: "...", data: []}]
    ReturnError --> End([结束])

    ParseResult --> CheckDataValid{数据有效?}
    CheckDataValid -->|有效| ProcessData[处理数据]
    CheckDataValid -->|无效| FormatError

    ProcessData --> End
```

## 5. 数据流图

```mermaid
flowchart LR
    A[用户问题] --> B[IntentService]
    B --> C{意图识别结果}
    C --> D[type: int]
    C --> E[results: List]
    C --> F[similarity: float]
    C --> G[database: str]

    D --> H{后处理逻辑}
    E --> H

    H -->|type=1| I[固定问题模板]
    H -->|type=2| J[提取results[1:4]]

    I --> K[推荐问题列表]
    J --> K

    K --> L[格式化为<br/>guess_your_question]
    L --> M[返回给前端]
```

## 6. 系统交互图

```mermaid
graph TB
    subgraph "前端层"
        A[用户界面]
    end

    subgraph "API层"
        B[/api/guess-questions]
        C[chat_routes.py]
    end

    subgraph "服务层"
        D[IntentService]
        E[后处理函数]
    end

    subgraph "数据层"
        F[RagflowClient]
        G[知识库]
    end

    A -->|HTTP POST| B
    B --> C
    C --> D
    D --> F
    F --> G
    G -->|查询结果| F
    F -->|意图识别结果| D
    D -->|意图结果| C
    C --> E
    E -->|推荐问题| C
    C -->|响应| B
    B -->|JSON| A
```

## 7. 状态转换图

```mermaid
stateDiagram-v2
    [*] --> 接收请求
    接收请求 --> 调用意图识别
    调用意图识别 --> 意图识别成功: 成功
    调用意图识别 --> 意图识别失败: 失败

    意图识别成功 --> 判断类别
    判断类别 --> 类别1处理: type=1
    判断类别 --> 类别2处理: type=2
    判断类别 --> 默认处理: 其他

    类别1处理 --> 返回固定问题
    类别2处理 --> 提取相关问题
    默认处理 --> 返回空列表

    返回固定问题 --> 格式化响应
    提取相关问题 --> 格式化响应
    返回空列表 --> 格式化响应

    格式化响应 --> 返回成功响应
    意图识别失败 --> 返回错误响应

    返回成功响应 --> [*]
    返回错误响应 --> [*]
```

## 8. 时序图（详细版）

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant F as 前端
    participant R as Router
    participant H as guess_questions_handler
    participant I as IntentService
    participant P1 as process_type1
    participant P2 as process_type2
    participant L as Logger

    U->>F: 输入问题
    F->>R: POST /api/guess-questions
    R->>H: 调用处理函数
    H->>L: 记录请求日志

    H->>I: process_query(question, user_id)
    I->>I: 查询知识库
    I-->>H: 返回意图结果
    H->>L: 记录意图识别结果

    alt type == 1
        H->>P1: 调用类别1处理函数
        P1->>P1: 获取固定问题模板
        P1-->>H: 返回3个固定问题
    else type == 2
        H->>P2: 调用类别2处理函数
        P2->>P2: 提取results[1:4]
        P2-->>H: 返回提取的问题
    end

    H->>H: 格式化为标准响应
    H->>L: 记录响应日志
    H-->>R: 返回响应
    R-->>F: JSON响应
    F-->>U: 展示推荐问题
```

## 流程说明

### 整体流程
1. 用户在前端输入问题
2. 前端调用 `/api/guess-questions` 接口
3. 接口调用 `IntentService.process_query()` 进行意图识别
4. 根据意图类型（type）选择不同的后处理函数
5. 格式化推荐问题列表并返回给前端
6. 前端展示推荐问题给用户

### 关键决策点
- **意图类型判断**：根据 `type` 字段决定使用哪种推荐策略
- **结果数量处理**：类别2需要处理结果不足3个的情况
- **错误处理**：捕获意图识别失败和数据格式错误

### 性能优化点
- 意图识别结果可以考虑缓存（后续优化）
- 固定问题模板可以预加载到内存
- 异步处理可以提升响应速度
