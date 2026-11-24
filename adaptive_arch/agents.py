from typing import Dict;

from .constants import V_流水线工序;


# 智能体基类：每个智能体有名字、角色和擅长领域，run 方法根据上下文产出一段内容。
# 这里的智能体是规则模拟的，不依赖大模型，保证开箱即用、可复现；
# 真实项目里可以把 run 换成 LLM 调用，接口不变。
class BaseAgent:
    def __init__(self, name: str, role: str, expertise: str):
        self.name = name;
        self.role = role;
        self.expertise = expertise;

    # 子类实现具体的产出逻辑，默认返回占位文本。
    def run(self, context: Dict) -> str:
        return f"[{self.name}] 暂无输出。";

    def __repr__(self):
        return f"<Agent {self.name}({self.role})>";


# 调研员：负责文献检索和资料收集。
class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("调研员", "信息收集", "文献检索、资料汇总");

    def run(self, context: Dict) -> str:
        task = context.get("task", "未知任务");
        return f"围绕「{task}」检索到 12 篇相关文献，整理出 3 个研究空白点。";


# 规划师：负责方案设计和任务拆解。
class PlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__("规划师", "方案设计", "实验设计、流程拆解");

    def run(self, context: Dict) -> str:
        return "提出两套可行方案，推荐方案 A：先小样本验证，再扩量实验。";


# 数据分析师：负责数据处理和异常排查。
class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__("数据分析师", "数据处理", "清洗、统计、可视化");

    def run(self, context: Dict) -> str:
        return "完成数据清洗与特征工程，输出 3 份统计图表。";


# 写作员：负责初稿撰写和成果整理。
class WritingAgent(BaseAgent):
    def __init__(self):
        super().__init__("写作员", "内容产出", "初稿撰写、格式编排");

    def run(self, context: Dict) -> str:
        return "完成初稿撰写，共 4 个章节，待评审。";


# 统计专家：在数据异常时被拉进会诊小组。
class StatisticsExpert(BaseAgent):
    def __init__(self):
        super().__init__("统计专家", "方法评审", "假设检验、显著性分析");

    def run(self, context: Dict) -> str:
        reason = context.get("blocked_reason", "数据异常");
        return f"针对「{reason}」，建议改用非参数检验并扩大样本量，结论可复现。";


# 领域专家：在结论矛盾时被拉进会诊小组。
class DomainExpert(BaseAgent):
    def __init__(self):
        super().__init__("领域专家", "领域研判", "背景知识、结论解读");

    def run(self, context: Dict) -> str:
        reason = context.get("blocked_reason", "结论矛盾");
        return f"结合领域背景，「{reason}」属于已知现象，修正解读后结论自洽。";


# 主持人：圆桌模式下控场，汇总各方观点给出收敛结论。
class ModeratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("主持人", "流程控场", "主持讨论、收敛结论");

    def run(self, context: Dict) -> str:
        return "汇总各方观点，形成一致方案：进入标准化执行阶段。";


# 主管：星型模式下的中心调度，把子任务派发给对应专家。
class DispatcherAgent(BaseAgent):
    def __init__(self):
        super().__init__("主管", "任务派发", "拆解任务、路由专家、汇总结果");

    def run(self, context: Dict) -> str:
        step = context.get("pipeline_step", 0);
        step_name = V_流水线工序[step] if step < len(V_流水线工序) else "收尾";
        return f"将「{step_name}」派发给对应专家，已回收并汇总结果。";


# 一次性构造所有角色，供各拓扑按需取用。
def build_all_agents() -> Dict[str, BaseAgent]:
    return {
        "research": ResearchAgent(),
        "planning": PlanningAgent(),
        "data": DataAgent(),
        "writing": WritingAgent(),
        "statistics": StatisticsExpert(),
        "domain": DomainExpert(),
        "moderator": ModeratorAgent(),
        "dispatcher": DispatcherAgent(),
    };
