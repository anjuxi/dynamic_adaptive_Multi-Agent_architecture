from typing import Any, Dict;

from .constants import (
    V_阶段_已完成,
    V_高优先级拓扑,
    V_最大切换次数,
    V_最大迭代步数,
    V_阶段拓扑映射,
    V_切换冷却步数,
    V_拓扑_结束,
    V_拓扑_流水线,
    V_兜底拓扑,
    V_流水线工序,
);
from .evaluator import RuleBasedEvaluator, StateEvaluator;
from .snapshot import append_snapshot, take_snapshot;
from .state import AdaptiveState, append_history;
from .switch_log import detect_oscillation, log_switch;


# 元调度器是整个自适应架构的大脑：持续感知任务状态，决定下一轮用哪种拓扑。
# 它本身不干活，只做决策——选拓扑、控切换、防震荡、做兜底。
# 博文里强调的"切换防抖、状态快照、防循环、兜底降级"都在这个类里实现。
class MetaScheduler:
    # 注入一个状态评估器，默认用规则版，生产环境可换成 LLM 版。
    def __init__(self, evaluator: StateEvaluator | None = None):
        self.evaluator = evaluator if evaluator is not None else RuleBasedEvaluator();

    # 核心决策方法：输入当前状态，返回对状态的增量更新（含 current_topology）。
    def decide(self, state: AdaptiveState) -> Dict[str, Any]:
        iteration = state.get("iteration", 0) + 1;
        phase = self.evaluator.evaluate(state);
        current = state.get("current_topology", V_拓扑_流水线);

        # 1. 先算基础目标拓扑：按阶段映射表查。
        target = V_阶段拓扑映射.get(phase, V_兜底拓扑);
        reason = f"任务阶段「{phase}」，切换到 {target}";

        # 2. 防循环：超过最大迭代步数，强制结束，避免无限跑下去。
        if iteration > V_最大迭代步数:
            target = V_拓扑_结束;
            reason = "达到最大迭代步数，强制结束";

        # 3. 兜底降级：切换次数超限，视为调度失控，锁到稳定拓扑。
        switch_count = state.get("switch_count", 0);
        forced_fallback = state.get("forced_fallback", False);
        if switch_count >= V_最大切换次数 and not forced_fallback:
            forced_fallback = True;
            target = V_兜底拓扑;
            reason = f"切换次数超限（{switch_count}），触发兜底降级到 {V_兜底拓扑}";
        elif forced_fallback:
            # 已经触发兜底，就锁在兜底拓扑上，除非任务完成或流水线跑完才放行结束。
            pipeline_done = state.get("pipeline_step", 0) >= len(V_流水线工序);
            if phase == V_阶段_已完成 or pipeline_done:
                target = V_拓扑_结束;
                reason = "兜底模式下任务已收尾，结束调度";
            else:
                target = V_兜底拓扑;
                reason = "兜底降级中，保持稳定拓扑运行";

        # 4. 震荡检测：最近几次切换在两个拓扑间来回横跳，就冻结切换。
        oscillating = detect_oscillation(state);

        # 5. 决定这一轮要不要真的切换。
        pending = state.get("pending_topology", "");
        streak = state.get("pending_streak", 0);
        # 兜底降级也走立即切换，不能被冷却卡住，否则失控时切不到稳定拓扑。
        high_priority = target in V_高优先级拓扑 or forced_fallback;
        should_switch = False;

        if target == current:
            # 目标和当前一致，不用切，清空待观察计数。
            pending = "";
            streak = 0;
        elif high_priority:
            # 高优先级切换（卡点要立刻会诊、完成要立刻结束）不经过冷却。
            should_switch = True;
        elif oscillating:
            # 检测到震荡，冻结切换，保持当前拓扑，打断来回横跳。
            should_switch = False;
            pending = target;
            streak = 0;
        else:
            # 普通切换：目标拓扑需要连续稳定 V_切换冷却步数 轮才放行，防抖。
            if target == pending:
                streak += 1;
            else:
                pending = target;
                streak = 1;
            should_switch = streak >= V_切换冷却步数;

        # 6. 应用决策。
        previous = state.get("previous_topology", "");
        switch_log = state.get("switch_log", []);
        snapshots = state.get("snapshots", []);
        last_switch_iter = state.get("last_switch_iter", -10);

        if should_switch:
            # 切换前先拍快照，方便回溯。
            snapshot = take_snapshot(state, reason);
            snapshots = append_snapshot(state, snapshot);
            switch_log = log_switch(state, current, target, reason);
            previous = current;
            current = target;
            switch_count += 1;
            last_switch_iter = iteration;
            pending = "";
            streak = 0;
            detail = f"拓扑切换：{previous} → {current}（{reason}）";
        elif target == current:
            detail = f"保持当前拓扑 {current}（{reason.replace('切换到', '目标即')}）";
        elif oscillating:
            detail = f"检测到拓扑震荡，冻结切换，保持 {current}（目标 {target}）";
        else:
            detail = f"目标拓扑 {target} 连续稳定 {streak}/{V_切换冷却步数} 轮，暂不切换，保持 {current}";

        history = append_history(state, {
            "iteration": iteration,
            "topology": "meta_scheduler",
            "detail": detail,
        });

        return {
            "iteration": iteration,
            "task_state": phase,
            "current_topology": current,
            "previous_topology": previous,
            "target_topology": target,
            "switch_count": switch_count,
            "last_switch_iter": last_switch_iter,
            "pending_topology": pending,
            "pending_streak": streak,
            "forced_fallback": forced_fallback,
            "history": history,
            "switch_log": switch_log,
            "snapshots": snapshots,
        };
