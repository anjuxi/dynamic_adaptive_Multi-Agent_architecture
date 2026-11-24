from typing import Any, Dict;

from ..agents import build_all_agents;
from ..state import AdaptiveState, append_history;


# 拓扑基类：每种协作模式都继承它，实现 execute 方法。
# execute 接收当前状态，模拟一轮该拓扑下的多智能体协作，返回对状态的增量更新。
# 这里的拓扑是"模拟实现"——LangGraph 原生不支持运行时重构图，
# 所以把每种拓扑做成一个可被元调度器选中的节点，内部再跑多智能体逻辑。
class BaseTopology:
    # 拓扑的唯一标识，和常量里的 V_拓扑_* 对应。
    name: str = "base";

    def __init__(self, agents: Dict[str, Any] | None = None):
        # 没传就构造全套角色，传了就用外部给的，方便测试替换。
        self.agents = agents if agents is not None else build_all_agents();

    # 子类实现：执行一轮协作，返回状态增量字典。
    def execute(self, state: AdaptiveState) -> Dict[str, Any]:
        raise NotImplementedError;

    # 给事件流追加一条本拓扑的执行记录，返回新的完整 history 列表。
    def _record(self, state: AdaptiveState, detail: str) -> list:
        return append_history(state, {
            "iteration": state.get("iteration", 0),
            "topology": self.name,
            "detail": detail,
        });
