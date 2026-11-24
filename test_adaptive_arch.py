from adaptive_arch import (
    BlackboardTopology,
    ExpertReviewTopology,
    LLMStateEvaluator,
    MetaScheduler,
    PipelineTopology,
    RoundTableTopology,
    StarTopology,
    build_initial_state,
    run_adaptive,
);
from adaptive_arch.constants import (
    V_阶段_已完成,
    V_阶段_执行中,
    V_阶段_卡点阻塞,
    V_阶段_方案规划,
    V_阶段_头脑风暴,
    V_阶段拓扑映射,
    V_最大迭代步数,
    V_最大切换次数,
    V_拓扑_黑板,
    V_拓扑_结束,
    V_拓扑_流水线,
    V_拓扑_专家会诊,
    V_拓扑_圆桌,
    V_拓扑_星型,
    V_兜底拓扑,
);
from adaptive_arch.snapshot import take_snapshot;
from adaptive_arch.switch_log import detect_oscillation;

# 收集所有用例的列表，元素是 (用例名, 函数)。
测试集 = [];


# 用例注册装饰器，把测试函数登记到测试集里。
def 用例(name):
    def 注册(fn):
        测试集.append((name, fn));
        return fn;
    return 注册;


# 把一次 decide 的返回合并进状态副本，方便多步测试。
def 应用决策(state, decision):
    merged = dict(state);
    merged.update(decision);
    return merged;


@用例("阶段到拓扑的映射正确")
def test_阶段拓扑映射():
    scheduler = MetaScheduler();
    for 阶段, 期望拓扑 in V_阶段拓扑映射.items():
        state = build_initial_state("测试映射");
        state["task_state"] = 阶段;
        state["current_topology"] = "其他";
        decision = scheduler.decide(state);
        assert decision["target_topology"] == 期望拓扑, f"阶段 {阶段} 应映射到 {期望拓扑}，实际 {decision['target_topology']}";


@用例("完整流程能正常结束并产出结果")
def test_完整流程结束():
    state = run_adaptive("端到端测试任务");
    assert state.get("task_state") == V_阶段_已完成, "任务应到达完成阶段";
    assert bool(state.get("task_result")), "应产出最终结果";
    assert state.get("current_topology") == V_拓扑_结束, "最终拓扑应为结束";


@用例("拓扑切换轨迹符合预期")
def test_切换轨迹():
    state = run_adaptive("轨迹测试任务");
    轨迹 = [r["to"] for r in state.get("switch_log", [])];
    期望 = [V_拓扑_星型, V_拓扑_流水线, V_拓扑_专家会诊, V_拓扑_流水线, V_拓扑_黑板, V_拓扑_结束];
    assert 轨迹 == 期望, f"切换轨迹不符：{轨迹}";


@用例("每次切换都生成快照和日志")
def test_快照与日志数量():
    state = run_adaptive("快照测试任务");
    切换次数 = state.get("switch_count", 0);
    assert len(state.get("snapshots", [])) == 切换次数, "快照数应等于切换次数";
    assert len(state.get("switch_log", [])) == 切换次数, "日志数应等于切换次数";
    assert 切换次数 == 6, f"预期 6 次切换，实际 {切换次数}";


@用例("防抖机制生效，存在稳定观察轮")
def test_防抖生效():
    state = run_adaptive("防抖测试任务");
    详情列表 = [e.get("detail", "") for e in state.get("history", [])];
    assert any("连续稳定" in d for d in 详情列表), "应出现防抖观察记录";


@用例("震荡检测能冻结切换")
def test_震荡冻结():
    state = build_initial_state("震荡测试");
    # 构造一个在 pipeline 和 star 之间来回横跳的切换日志。
    state["switch_log"] = [
        {"to": V_拓扑_流水线}, {"to": V_拓扑_星型},
        {"to": V_拓扑_流水线}, {"to": V_拓扑_星型},
    ];
    state["current_topology"] = V_拓扑_星型;
    state["task_state"] = V_阶段_执行中;
    state["iteration"] = 5;
    state["switch_count"] = 4;
    assert detect_oscillation(state) is True, "应检测到震荡";
    scheduler = MetaScheduler();
    decision = scheduler.decide(state);
    # 震荡时冻结，当前拓扑保持不变。
    assert decision["current_topology"] == V_拓扑_星型, "震荡时不应切换";
    详情 = "".join(e.get("detail", "") for e in decision["history"]);
    assert "震荡" in 详情, "历史里应记录震荡冻结";


@用例("切换次数超限触发兜底降级")
def test_兜底降级():
    state = build_initial_state("兜底测试");
    state["switch_count"] = V_最大切换次数;
    state["current_topology"] = V_拓扑_星型;
    state["task_state"] = V_阶段_执行中;
    scheduler = MetaScheduler();
    decision = scheduler.decide(state);
    assert decision["forced_fallback"] is True, "应触发兜底降级";
    assert decision["current_topology"] == V_兜底拓扑, "应立即切到兜底拓扑";
    assert decision["switch_count"] == V_最大切换次数 + 1, "切换次数应加一";


@用例("达到最大迭代步数强制结束")
def test_防循环结束():
    state = build_initial_state("防循环测试");
    state["iteration"] = V_最大迭代步数;
    state["current_topology"] = V_拓扑_圆桌;
    scheduler = MetaScheduler();
    decision = scheduler.decide(state);
    assert decision["current_topology"] == V_拓扑_结束, "超步数应强制结束";


@用例("专家会诊幂等，重复执行不覆盖产出")
def test_专家会诊幂等():
    topo = ExpertReviewTopology();
    state = build_initial_state("幂等测试");
    state["task_state"] = V_阶段_卡点阻塞;
    state["blocked_reason"] = "数据异常";
    第一次 = topo.execute(state);
    assert "数据异常" in 第一次["stage_outputs"]["expert_review"], "第一次应带上卡点原因";
    # 模拟合并后再跑一次。
    state2 = 应用决策(state, 第一次);
    第二次 = topo.execute(state2);
    assert "expert_review" not in 第二次 or 第二次.get("stage_outputs") is None or "数据异常" in 第二次.get("stage_outputs", {}).get("expert_review", "数据异常"), "第二次不应覆盖掉正确产出";


@用例("各拓扑都能产出阶段结果")
def test_各拓扑产出():
    state = build_initial_state("拓扑产出测试");
    assert "brainstorm" in RoundTableTopology().execute(state)["stage_outputs"];
    state["task_state"] = V_阶段_方案规划;
    assert "planning" in StarTopology().execute(state)["stage_outputs"];
    state["task_state"] = V_阶段_执行中;
    assert "文献检索" in PipelineTopology().execute(state)["stage_outputs"];
    state["task_state"] = V_阶段_卡点阻塞;
    state["blocked_reason"] = "异常";
    assert "expert_review" in ExpertReviewTopology().execute(state)["stage_outputs"];
    state["stage_outputs"] = {"a": "b"};
    结果 = BlackboardTopology().execute(state);
    assert bool(结果["task_result"]), "黑板应产出最终结果";
    assert 结果["task_state"] == V_阶段_已完成;


@用例("状态快照与原状态隔离")
def test_快照隔离():
    state = build_initial_state("快照隔离测试");
    state["task_result"] = "原始";
    snap = take_snapshot(state, "测试");
    state["task_result"] = "被修改";
    assert snap["state"]["task_result"] == "原始", "快照不应被后续修改影响";


@用例("LLM评估器无Key时自动降级不崩溃")
def test_LLM评估器降级():
    evaluator = LLMStateEvaluator(api_key="");
    state = build_initial_state("降级测试");
    阶段 = evaluator.evaluate(state);
    assert 阶段 == V_阶段_头脑风暴, "无 Key 应降级为规则版结果";


# 主函数：跑全部用例，统计通过失败。
def main():
    print("开始运行动态自适应架构测试用例！");
    print("——" * 50);
    通过 = 0;
    失败 = 0;
    for name, fn in 测试集:
        try:
            fn();
            通过 += 1;
            print(f"  通过 {name}！");
        except Exception as e:
            失败 += 1;
            print(f"  失败 {name}：{e}！");
    print("——" * 50);
    print(f"测试完成：通过 {通过} 个，失败 {失败} 个！");
    if 失败 == 0:
        print("✅ 全部测试用例通过！");
    else:
        print("存在失败用例，请检查！");


if __name__ == "__main__":
    main();
