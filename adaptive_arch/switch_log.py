from datetime import datetime;
from typing import Any, Dict, List;


# 记录一次拓扑切换，返回新的完整切换日志列表（LangGraph 按整键替换合并）。
# from_topology 是切换前的拓扑，to_topology 是切换后的拓扑，reason 说明为什么切。
def log_switch(state: Dict[str, Any], from_topology: str, to_topology: str, reason: str) -> List[Dict[str, Any]]:
    record = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "iteration": state.get("iteration", 0),
        "from": from_topology,
        "to": to_topology,
        "reason": reason,
    };
    switch_log = list(state.get("switch_log", []));
    switch_log.append(record);
    return switch_log;


# 统计某个拓扑被切换进入了多少次，用来判断是否在两个拓扑间来回震荡。
def count_switches_to(state: Dict[str, Any], topology: str) -> int:
    return sum(1 for r in state.get("switch_log", []) if r.get("to") == topology);


# 检测最近 N 次切换是否在两个拓扑之间反复横跳，是则视为震荡。
def detect_oscillation(state: Dict[str, Any], window: int = 4) -> bool:
    records = state.get("switch_log", []);
    if len(records) < window:
        return False;
    recent = records[-window:];
    targets = [r["to"] for r in recent];
    # 窗口内只出现两个不同拓扑，且交替出现，就是典型的来回震荡。
    unique = set(targets);
    if len(unique) != 2:
        return False;
    a, b = list(unique);
    expected = [a, b] * (window // 2);
    return targets == expected or targets == ([b, a] * (window // 2));
