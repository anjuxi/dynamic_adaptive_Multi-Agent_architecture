from typing import Any, Dict;

from ..constants import V_卡点工序, V_阶段_评审中, V_阶段_执行中, V_阶段_卡点阻塞, V_流水线工序;
from ..state import AdaptiveState;
from .base import BaseTopology;


# 流水线拓扑：按固定工序串行推进，每道工序由对应专家负责。
# 适用于方案定稿后的标准化执行阶段，调试简单、确定性强。
# 在「数据处理」这道工序会模拟一次数据异常，用来触发专家会诊，演示动态切换。
class PipelineTopology(BaseTopology):
    name = "pipeline";

    # 工序到负责智能体的映射。
    V_工序负责人 = {
        "文献检索": "research",
        "实验设计": "planning",
        "数据处理": "data",
        "初稿撰写": "writing",
    };

    def execute(self, state: AdaptiveState) -> Dict[str, Any]:
        steps = V_流水线工序;
        step = state.get("pipeline_step", 0);
        context = {"task": state.get("task", ""), "blocked_reason": state.get("blocked_reason", "")};

        # 工序全部跑完，进入评审阶段。
        if step >= len(steps):
            history = self._record(state, "流水线工序全部完成，进入评审阶段");
            return {"task_state": V_阶段_评审中, "history": history};

        step_name = steps[step];
        agent = self.agents[self.V_工序负责人[step_name]];
        output = agent.run(context);
        stage_outputs = dict(state.get("stage_outputs", {}));
        stage_outputs[step_name] = f"{agent.name}：{output}";
        new_step = step + 1;

        # 命中卡点工序：模拟数据异常，阻塞当前任务，等待专家会诊。
        if step_name == V_卡点工序:
            history = self._record(state, f"流水线推进到「{step_name}」，发现数据异常，触发卡点");
            return {
                "task_state": V_阶段_卡点阻塞,
                "blocked_reason": "实验数据出现异常波动，统计结论待验证",
                "pipeline_step": new_step,
                "stage_outputs": stage_outputs,
                "history": history,
            };
        # 全部工序跑完，进入评审。
        if new_step >= len(steps):
            history = self._record(state, f"流水线完成「{step_name}」，全部工序结束");
            return {
                "task_state": V_阶段_评审中,
                "pipeline_step": new_step,
                "stage_outputs": stage_outputs,
                "history": history,
            };
        # 正常推进到下一道工序。
        history = self._record(state, f"流水线完成「{step_name}」，继续下一道工序");
        return {
            "task_state": V_阶段_执行中,
            "pipeline_step": new_step,
            "stage_outputs": stage_outputs,
            "history": history,
        };
