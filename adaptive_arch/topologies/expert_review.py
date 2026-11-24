from typing import Any, Dict;

from ..constants import V_阶段_执行中;
from ..state import AdaptiveState;
from .base import BaseTopology;


# 专家会诊拓扑：执行中遇到卡点时，元调度器临时拉起相关专家组成会诊小组。
# 这是一种"临时搭、用完再拆"的协作模式，体现动态自适应的灵活性。
class ExpertReviewTopology(BaseTopology):
    name = "expert_review";

    def execute(self, state: AdaptiveState) -> Dict[str, Any]:
        # 幂等守卫：已经会诊解决过就不再重复跑，避免防抖观察轮覆盖掉正确产出。
        if state.get("expert_resolved"):
            history = self._record(state, "专家会诊已完成，保持当前状态");
            return {"task_state": V_阶段_执行中, "history": history};
        context = {
            "task": state.get("task", ""),
            "blocked_reason": state.get("blocked_reason", "未知卡点"),
        };
        # 会诊小组：统计专家 + 领域专家 + 数据分析师，共同排查卡点。
        members = ["statistics", "domain", "data"];
        outputs = [];
        for key in members:
            agent = self.agents.get(key);
            if agent is not None:
                outputs.append(f"{agent.name}：{agent.run(context)}");
        summary = "\n".join(outputs);
        stage_outputs = dict(state.get("stage_outputs", {}));
        stage_outputs["expert_review"] = summary;
        history = self._record(state, "专家会诊完成，卡点已解决");
        # 会诊结束，清除卡点，回归执行阶段。
        return {
            "task_state": V_阶段_执行中,
            "blocked_reason": "",
            "expert_resolved": True,
            "stage_outputs": stage_outputs,
            "history": history,
        };
