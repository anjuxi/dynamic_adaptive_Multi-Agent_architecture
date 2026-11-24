from typing import Any, Dict;

from ..constants import V_阶段_方案规划;
from ..state import AdaptiveState;
from .base import BaseTopology;


# 圆桌协商拓扑：多个对等智能体轮流发言，主持人最后收敛。
# 适用于任务初期信息不足、需要发散讨论的阶段，对应博文里的"头脑风暴"。
class RoundTableTopology(BaseTopology):
    name = "round_table";

    def execute(self, state: AdaptiveState) -> Dict[str, Any]:
        context = {"task": state.get("task", "")};
        # 参会角色：调研员先给信息，规划师和领域专家各抒己见，主持人收敛。
        speakers = ["research", "planning", "domain", "moderator"];
        outputs = [];
        for key in speakers:
            agent = self.agents.get(key);
            if agent is not None:
                outputs.append(f"{agent.name}：{agent.run(context)}");
        summary = "\n".join(outputs);
        # 圆桌结束意味着方案已定稿，进入规划/派发阶段。
        stage_outputs = dict(state.get("stage_outputs", {}));
        stage_outputs["brainstorm"] = summary;
        history = self._record(state, "圆桌协商完成，形成一致方案");
        return {
            "task_state": V_阶段_方案规划,
            "stage_outputs": stage_outputs,
            "history": history,
        };
