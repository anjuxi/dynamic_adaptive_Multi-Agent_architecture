from adaptive_arch import run_adaptive;


# 打印一条分隔线，统一输出风格。
def 分隔():
    print("——" * 50);


# 主函数：跑一轮完整的自适应调度演示，并把过程打印出来。
def main():
    # 演示任务：模拟博文里的自主科研 Agent 集群拿到一个全新课题。
    V_演示任务 = "自主科研集群：研究低功耗传感器网络的数据异常检测方法";
    print(f"启动动态自适应多智能体系统！");
    print(f"任务：{V_演示任务}！");
    分隔();

    # 运行自适应调度，拿到最终状态。
    state = run_adaptive(V_演示任务);

    # 打印拓扑切换轨迹，这是动态自适应最直观的体现。
    print("拓扑切换轨迹：");
    switch_log = state.get("switch_log", []);
    if not switch_log:
        print("（无切换记录）！");
    for i, record in enumerate(switch_log, 1):
        print(f"  {i}. [{record['time']}] 第{record['iteration']}轮 {record['from']} → {record['to']}  （{record['reason']}）！");
    分隔();

    # 打印每一轮的执行事件，能看到元调度器的决策和各拓扑的产出。
    print("执行事件流：");
    for event in state.get("history", []):
        topo = event.get("topology", "");
        detail = event.get("detail", "");
        print(f"  [第{event.get('iteration', '?')}轮] {topo}: {detail}！");
    分隔();

    # 打印各阶段产出。
    print("各阶段产出：");
    for stage_name, content in state.get("stage_outputs", {}).items():
        first_line = str(content).split("\n")[0];
        print(f"  [{stage_name}] {first_line}！");
    分隔();

    # 打印最终交付结果。
    print("最终交付结果：");
    print(state.get("task_result", "（无结果）"));
    分隔();

    # 打印统计摘要。
    print("运行统计：");
    print(f"  总迭代轮数：{state.get('iteration', 0)}！");
    print(f"  拓扑切换次数：{state.get('switch_count', 0)}！");
    print(f"  状态快照数：{len(state.get('snapshots', []))}！");
    print(f"  是否触发兜底降级：{state.get('forced_fallback', False)}！");
    print(f"  最终任务阶段：{state.get('task_state', '')}！");
    分隔();
    print("✅ 动态自适应调度演示完成！");


if __name__ == "__main__":
    main();
