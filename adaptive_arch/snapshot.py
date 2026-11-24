import copy;
from typing import Any, Dict, List;

from .constants import V_快照最大保留;


# 状态快照工具：每次拓扑切换前保存一份完整状态，方便出问题时回溯排查。
# 博文落地建议里明确要求每次切换都保存状态快照，这里用深拷贝保证快照不受后续修改影响。
def take_snapshot(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "iteration": state.get("iteration", 0),
        "task_state": state.get("task_state", ""),
        "topology": state.get("current_topology", ""),
        "reason": reason,
        "state": copy.deepcopy(state),
    };


# 把一份快照追加到状态的快照列表里，返回新的完整列表（LangGraph 按整键替换）。
def append_snapshot(state: Dict[str, Any], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    snapshots = list(state.get("snapshots", []));
    snapshots.append(snapshot);
    # 超过上限就丢掉最旧的，只留最近的，防止内存无限增长。
    if len(snapshots) > V_快照最大保留:
        snapshots.pop(0);
    return snapshots;


# 取出最近一份快照，供调试或回滚查看。
def latest_snapshot(state: Dict[str, Any]) -> Dict[str, Any] | None:
    snapshots = state.get("snapshots", []);
    return snapshots[-1] if snapshots else None;
