from typing import Any, Dict, List, TypedDict;

from .constants import V_阶段_头脑风暴, V_拓扑_圆桌;


# 自适应状态是整张图在节点之间传递的共享数据结构。
# 所有节点都读写这个字典，元调度器依据它判断下一轮该切到哪种拓扑。
# total=False 表示所有字段都是可选的，LangGraph 的增量合并才能正常工作。
class AdaptiveState(TypedDict, total=False):
    task: str;                       # 原始任务描述。
    task_state: str;                 # 当前任务阶段，对应 V_阶段_* 常量。
    current_topology: str;           # 当前正在使用的拓扑。
    previous_topology: str;          # 上一个拓扑，切换日志要用。
    target_topology: str;            # 元调度器评估出来的目标拓扑。
    task_result: str;                # 最终产出结果。
    stage_outputs: Dict[str, str];   # 各阶段的产出，键是阶段名。
    history: List[Dict[str, Any]];   # 执行事件流，记录每一步发生了什么。
    switch_count: int;               # 累计拓扑切换次数。
    iteration: int;                  # 累计迭代步数。
    snapshots: List[Dict[str, Any]]; # 每次切换时保存的状态快照。
    switch_log: List[Dict[str, Any]];# 拓扑切换日志。
    blocked_reason: str;             # 当前卡点原因，没有卡点时为空串。
    last_switch_iter: int;           # 上次切换发生在第几步，用于冷却判定。
    pending_topology: str;           # 正在观察是否稳定的目标拓扑。
    pending_streak: int;             # 目标拓扑连续稳定的轮数。
    forced_fallback: bool;           # 是否已经触发过兜底降级。
    pipeline_step: int;              # 流水线当前推进到第几道工序。
    expert_resolved: bool;           # 专家会诊是否已经解决过卡点。


# 构造一个初始状态，外部只需要传入任务描述即可。
def build_initial_state(task: str) -> AdaptiveState:
    # 初始阶段是头脑风暴，信息不足时先发散讨论，所以默认拓扑是圆桌。
    return {
        "task": task,
        "task_state": V_阶段_头脑风暴,
        "current_topology": V_拓扑_圆桌,
        "previous_topology": "",
        "target_topology": V_拓扑_圆桌,
        "task_result": "",
        "stage_outputs": {},
        "history": [],
        "switch_count": 0,
        "iteration": 0,
        "snapshots": [],
        "switch_log": [],
        "blocked_reason": "",
        "last_switch_iter": -10,
        "pending_topology": "",
        "pending_streak": 0,
        "forced_fallback": False,
        "pipeline_step": 0,
        "expert_resolved": False,
    };


# 往事件流里追加一条记录，返回新的完整列表（LangGraph 是按键替换合并的）。
def append_history(state: AdaptiveState, event: Dict[str, Any]) -> List[Dict[str, Any]]:
    history = list(state.get("history", []));
    history.append(event);
    return history;
