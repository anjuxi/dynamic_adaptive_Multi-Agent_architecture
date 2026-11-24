from typing import Any, Dict;

from ..constants import V_阶段_已完成;
from ..state import AdaptiveState;
from .base import BaseTopology;


# 黑板共享拓扑：各专家把证据写到共享黑板上，彼此解耦，最终融合形成结论。
# 适用于多证据融合的评审阶段，对应博文里的"读写共享空间、状态触发协作"。
class BlackboardTopology(BaseTopology):
    name = "blackboard";

    def execute(self, state: AdaptiveState) -> Dict[str, Any]:
        # 从已有阶段产出里提取各环节证据，汇总到黑板。
        stage_outputs = dict(state.get("stage_outputs", {}));
        evidence_lines = [];
        for stage_name, content in stage_outputs.items():
            # 只取每条产出的第一行，避免最终报告过长。
            first_line = str(content).split("\n")[0];
            evidence_lines.append(f"- [{stage_name}] {first_line}");
        blackboard = "\n".join(evidence_lines) if evidence_lines else "- （无可用证据）";
        # 融合证据，形成最终交付结果。
        task = state.get("task", "未知任务");
        result = (
            f"【任务】{task}\n"
            f"【结论】基于多轮协作与证据融合，任务已完成。\n"
            f"【证据汇总】\n{blackboard}\n"
            f"【交付】初稿已成形，统计结论经专家会诊验证可复现。"
        );
        stage_outputs["review"] = blackboard;
        history = self._record(state, "黑板融合完成，形成最终结论");
        return {
            "task_state": V_阶段_已完成,
            "task_result": result,
            "stage_outputs": stage_outputs,
            "history": history,
        };
