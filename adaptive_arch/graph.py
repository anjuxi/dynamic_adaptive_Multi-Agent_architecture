from typing import Any, Dict;

from langgraph.graph import END, StateGraph;

from .agents import build_all_agents;
from .constants import V_拓扑_结束;
from .evaluator import StateEvaluator;
from .meta_scheduler import MetaScheduler;
from .state import AdaptiveState, append_history, build_initial_state;
from .topologies import V_拓扑注册表, BaseTopology;


# 构建顶层自适应图。
# LangGraph 原生是静态图，所以这里用"条件边 + 拓扑节点"的方式模拟动态切换：
# 元调度器节点算出 current_topology，条件边据此把流转路由到对应拓扑节点，
# 拓扑节点跑完再回到元调度器，如此循环直到元调度器选出结束。
def build_adaptive_graph(evaluator: StateEvaluator | None = None) -> Any:
    agents = build_all_agents();
    scheduler = MetaScheduler(evaluator=evaluator);
    # 每个拓扑实例化一次，共享同一套智能体池。
    topologies: Dict[str, BaseTopology] = {
        name: cls(agents=agents) for name, cls in V_拓扑注册表.items()
    };

    builder = StateGraph(AdaptiveState);

    # 元调度器节点：只做决策，更新 current_topology 等字段。
    def meta_node(state: AdaptiveState) -> Dict[str, Any]:
        return scheduler.decide(state);

    # 拓扑节点：执行该拓扑的一轮协作。
    def make_runner(topo: BaseTopology):
        def runner(state: AdaptiveState) -> Dict[str, Any]:
            return topo.execute(state);
        return runner;

    # 收尾节点：写一条完成记录，保证历史完整。
    def finalize_node(state: AdaptiveState) -> Dict[str, Any]:
        history = append_history(state, {
            "iteration": state.get("iteration", 0),
            "topology": "finalize",
            "detail": "调度结束，任务完成",
        });
        return {"history": history};

    # 注册节点。
    builder.add_node("meta_scheduler", meta_node);
    for name, topo in topologies.items():
        builder.add_node(name, make_runner(topo));
    builder.add_node("finalize", finalize_node);

    builder.set_entry_point("meta_scheduler");

    # 条件边：按元调度器选出的拓扑路由。
    def route_by_topology(state: AdaptiveState) -> str:
        current = state.get("current_topology", V_拓扑_结束);
        if current == V_拓扑_结束:
            return "finalize";
        return current;

    route_map = {name: name for name in topologies};
    route_map["finalize"] = "finalize";
    builder.add_conditional_edges("meta_scheduler", route_by_topology, route_map);

    # 每个拓扑节点跑完都回到元调度器重新评估。
    for name in topologies:
        builder.add_edge(name, "meta_scheduler");
    builder.add_edge("finalize", END);

    return builder.compile();


# 便捷入口：给一个任务描述，跑完整轮自适应调度，返回最终状态。
def run_adaptive(task: str, evaluator: StateEvaluator | None = None, recursion_limit: int = 50) -> AdaptiveState:
    graph = build_adaptive_graph(evaluator=evaluator);
    initial = build_initial_state(task);
    final_state = graph.invoke(initial, config={"recursion_limit": recursion_limit});
    return final_state;
