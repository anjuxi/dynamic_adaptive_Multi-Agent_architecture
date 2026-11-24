from typing import Any, Dict;

from ..constants import V_阶段_执行中;
from ..state import AdaptiveState;
from .base import BaseTopology;


# 星型中心化拓扑：中心主管负责拆解任务、派发给对应专家、汇总结果。
# 专家之间不直接通信，所有信息流都经过主管，路由灵活。
class StarTopology(BaseTopology):
    name = "star";

    def execute(self, state: AdaptiveState) -> Dict[str, Any]:
        context = {"task": state.get("task", ""), "pipeline_step": state.get("pipeline_step", 0)};
        dispatcher = self.agents["dispatcher"];
        # 主管先拆解，再把规划环节的子任务派给规划师。
        dispatch_note = dispatcher.run(context);
        planning_note = self.agents["planning"].run(context);
        summary = f"{dispatch_note}\n规划师：{planning_note}";
        stage_outputs = dict(state.get("stage_outputs", {}));
        stage_outputs["planning"] = summary;
        history = self._record(state, "星型调度完成，主管派发并汇总规划结果");
        # 规划完成，进入标准化执行阶段。
        return {
            "task_state": V_阶段_执行中,
            "stage_outputs": stage_outputs,
            "history": history,
        };
