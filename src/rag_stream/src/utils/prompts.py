"""
SourceDispatchPrompts - 资源调度提示词管理
负责管理资源调度相关的所有提示词模板
"""

from rag_stream.models.schemas import AccidentEventData


class SourceDispatchPrompts:
    """资源调度提示词管理类"""

    @staticmethod
    def get_intent_classification_prompt(user_question: str) -> str:
        """
        获取意图分类提示词

        Args:
            user_question: 用户的问题文本

        Returns:
            str: 格式化后的提示词
        """
        return f"""你是一个资源调度专家，请你判断用户的意图。

【判断规则】
返回 "resource" 的情况（用户明确指定了具体资源）：
- 物品资源：指定了具体物品名称，如"给我酒精棉"、"需要纱布和绷带"、"给我防护服"
- 人员资源：指定了具体人名或队伍名称，如"张三专家"、"李四局长"、"王五救援队"
- 设施资源：指定了具体设施的完整名称，如"联系市中心消防站"、"找到东区污水处理厂"、"我要去东区人民医院"
  注意：即使使用"去"、"联系"等动词，只要指定了完整的具体名称（如"东区人民医院"），就应该返回resource

返回 "requirement" 的情况（用户需求模糊，需要系统推荐）：
- 位置查询：包含"最近的"、"附近"、"哪里有"等位置相关词汇，如"最近的医院在哪里"、"帮我找到最近的消防站"、"附近有避难场所吗"
- 模糊描述：使用"XX医院"、"XX设施"、"某个医院"等不明确的占位符或泛指词汇，如"我要去XX医院"、"找到XX污水处理厂"
- 事故求助：描述事故或伤害情况，如"我遇到了火灾"、"我被化学品腐蚀了怎么办"、"发生交通事故了"
- 泛指需求：使用"专业"、"合适的"等修饰词但不指定具体对象，如"需要专业救援人员"、"需要救援"

【关键判断点】
1. 如果用户提到具体的完整名称（人名、物品名、设施全称）→ resource
2. 如果用户询问位置（最近、附近、哪里）→ requirement
3. 如果用户使用占位符（XX、某个）或泛指词汇 → requirement
4. 如果用户只描述需求类型而不指定具体对象 → requirement
5. 动词不影响判断：无论使用"给我"、"找到"、"去"、"联系"等动词，关键看是否指定了具体完整名称

【输出要求】
只返回 "resource" 或 "requirement"，不返回其他任何解释性内容或思考过程。

用户的问题：{user_question}
"""

    @staticmethod
    def get_accident_type_classification_prompt(accident_data: AccidentEventData) -> str:
        """
        获取事故类型分类提示词

        Args:
            accident_data: 事故事件数据

        Returns:
            str: 格式化后的提示词
        """
        return f"""请你根据事故的信息，给出事故的类型序号，以下是事故类型的参考：
1：灾害事故救援
2：危化品泄漏救援
3：交通事故救援
4：水上救援
5：山地救援
6：公共卫生事件救援
7：其他领域
注意，只输出数字，其他任何内容都不要输出
以下是事故内容：
{accident_data.to_json_str()}"""

    @staticmethod
    def get_database_id_extraction_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取数据库ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请结合用户的问题，返回对应数据库中的ID值；如果不明确用户的意图，请按顺序返回所有ID；
提示：针对有位置信息的数据库信息，都是按照与事故位置由近到远排序的
<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""

    @staticmethod
    def get_entity_extraction_prompt(query: str) -> str:
        """
        获取实体提取提示词

        Args:
            query: 用户的问题文本

        Returns:
            str: 格式化后的提示词
        """
        return f"""你是一个专业的分词专家，请把用户问题中提及的所有实体名称都拆解出来，以List<str>的格式输出
<用户问题>
{query}
</用户问题>

<输出示例>
["绷带","张三专家","消防设施"]
</输出示例>
"""

    @staticmethod
    def get_emergency_supplies_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取应急物资ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的应急物资ID。
筛选原则：
1. 优先匹配用户明确提到的物资名称
2. 考虑事故类型和危化品信息，选择相关的应急物资
3. 如果用户未明确指定，返回3个最相关的物资ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""

    @staticmethod
    def get_rescue_team_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取救援队伍ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的救援队伍ID。
筛选原则：
1. 优先匹配用户明确提到的队伍名称
2. 根据事故类型选择专业对口的救援队伍（如化学品泄漏选择危化品救援队）
3. 考虑队伍的业务领域和专业能力
4. 数据库信息已按距离排序，优先选择距离较近的队伍
5. 如果用户未明确指定，返回前3个最相关的队伍ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""

    @staticmethod
    def get_emergency_expert_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取应急专家ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的应急专家ID。
筛选原则：
1. 优先匹配用户明确提到的专家姓名
2. 根据事故类型选择专业对口的专家（如危化品事故选择化学品专家）
3. 考虑专家的业务领域和专业方向
4. 如果用户未明确指定，返回前2-3个最相关的专家ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""

    @staticmethod
    def get_fire_fighting_facilities_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取消防设施ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的消防设施ID。
筛选原则：
1. 优先匹配用户明确提到的设施名称
2. 数据库信息已按距离排序，优先选择距离事故地点最近的设施
3. 如果用户询问"最近的消防设施"，返回前3个最近的设施ID
4. 如果用户未明确指定，返回前5个最近的设施ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""

    @staticmethod
    def get_shelter_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取避难场所ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的避难场所ID。
筛选原则：
1. 优先匹配用户明确提到的场所名称
2. 数据库信息已按距离排序，优先选择距离事故地点最近的避难场所
3. 如果用户询问"最近的避难场所"或"疏散地点"，返回前3个最近的场所ID
4. 考虑避难场所的容量和适用场景
5. 如果用户未明确指定，返回前5个最近的场所ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""

    @staticmethod
    def get_medical_institution_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取医疗机构ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的医疗机构ID。
筛选原则：
1. 优先匹配用户明确提到的医疗机构名称
2. 根据事故类型选择专业对口的医疗机构（如化学品灼伤选择有毒物救治能力的医院）
3. 考虑医疗机构的专业能力和救治水平
4. 如果用户询问"最近的医院"，优先选择距离较近的医疗机构
5. 如果用户未明确指定，返回前3个最相关的医疗机构ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""
    @staticmethod
    def get_rescue_organization_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取救援机构ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的救援机构ID。
筛选原则：
1. 优先匹配用户明确提到的机构名称
2. 根据事故类型选择专业对口的救援机构
3. 数据库信息已按距离排序，优先选择距离较近的机构
4. 考虑机构的救援能力和资源配置
5. 如果用户未明确指定，返回前3个最相关的救援机构ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""


class GuessQuestionsPrompts:
    """猜你想问提示词管理类"""

    @staticmethod
    def get_type2_fallback_prompt(user_question: str) -> str:
        """type2 无检索结果时的大模型兜底提示词"""
        return f"""你是“猜你想问”推荐器，不是回答器。

你的任务：
基于用户当前问题，预测“用户下一步可能还会问的3个问题”。

必须遵守：
1. 只输出3条问题，且每条都是中文问句。
2. 问题要站在用户视角，像用户会继续搜索/提问的内容。
3. 聚焦下一步决策信息（如：处置步骤、防护措施、就医判断、上报对象、应急物资）。
4. 每条尽量简洁，避免与原问题重复表达。

严格禁止：
1. 回答用户原问题。
2. 输出解释、建议、前言、总结、标题。
3. 使用“您是在……吗”“请问……”这类客服追问口吻。
4. 输出除 JSON 数组外的任何内容。

输出格式（必须完全一致为JSON数组）：
["问题1", "问题2", "问题3"]

示例（仅帮助理解风格）：
用户问题：我碰到了氢氟酸怎么办？
可输出：
["氢氟酸接触后需要马上去医院吗？", "皮肤被氢氟酸灼伤后现场怎么处理？", "处理氢氟酸泄漏需要哪些防护装备？"]

当前用户问题：{user_question}
"""

    @staticmethod
    def get_protection_target_prompt(voice_text: str, accent_result: str) -> str:
        """
        获取防护目标ID提取提示词

        Args:
            voice_text: 用户的问题文本
            accent_result: 事故信息

        Returns:
            str: 格式化后的提示词
        """
        return f"""
请根据用户的问题和事故信息，从数据库中筛选出最合适的防护目标ID。
筛选原则：
1. 优先匹配用户明确提到的目标名称
2. 数据库信息已按距离排序，优先选择距离事故地点最近的防护目标
3. 根据事故类型和危化品信息，识别可能受影响的防护目标
4. 考虑防护目标的重要性和敏感性（如学校、医院、居民区等）
5. 如果用户未明确指定，返回前5个最近或最重要的防护目标ID

<用户问题>
{voice_text}
</用户问题>

<事故信息>
{accent_result}
</事故信息>

<数据库信息>

</数据库信息>

<返回结构>
[{{"id":"1111"}},{{"id":"2222"}}]
</返回结构>
"""
