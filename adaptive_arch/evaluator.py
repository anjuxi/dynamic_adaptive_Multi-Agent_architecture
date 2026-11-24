import os;
from typing import Optional;

from .constants import V_阶段_已完成;
from .state import AdaptiveState;


# 状态评估器的基类。元调度器不自己猜阶段，而是交给评估器给出当前任务阶段。
# 这样规则版和 LLM 版可以互换，符合博文里"生产级一般用 LLM 做状态评估"的思路。
class StateEvaluator:
    # 子类实现：根据当前状态返回任务阶段常量。
    def evaluate(self, state: AdaptiveState) -> str:
        raise NotImplementedError;


# 规则版评估器：直接信任状态里已经记录的阶段，再用结果字段做一次兜底校验。
class RuleBasedEvaluator(StateEvaluator):
    def evaluate(self, state: AdaptiveState) -> str:
        # 已经产出最终结果，就视为完成，避免卡在评审阶段不退出。
        if state.get("task_result"):
            return V_阶段_已完成;
        # 否则按状态里记录的阶段走，没有记录就保持头脑风暴。
        return state.get("task_state") or "brainstorm";


# 可选的 LLM 版评估器：让大模型根据历史和产出判断当前阶段。
# 没配 API Key 时不会报错，而是自动降级到规则版，保证开箱即用。
class LLMStateEvaluator(StateEvaluator):
    # api_key 和 base_url 都支持从环境变量读，也支持构造时直接传。
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "");
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1");
        self.model = model;
        self._fallback = RuleBasedEvaluator();

    # 判断 LLM 能不能用，不能用就走规则版。
    def _available(self) -> bool:
        return bool(self.api_key);

    def evaluate(self, state: AdaptiveState) -> str:
        if not self._available():
            return self._fallback.evaluate(state);
        # 真正调用 LLM 的逻辑放在这里，按 OpenAI 兼容格式请求。
        # 这里用 try 包一下，任何异常都降级，不让评估器把整个调度拖垮。
        try:
            return self._call_llm(state);
        except Exception:
            return self._fallback.evaluate(state);

    # 组装提示词并请求大模型，返回解析出的阶段常量。
    def _call_llm(self, state: AdaptiveState) -> str:
        import json;
        import urllib.request;

        history = state.get("history", []);
        recent = history[-5:] if len(history) > 5 else history;
        prompt = (
            "你是一个多智能体系统的状态评估器。根据任务和最近执行记录，"
            "判断当前任务处于哪个阶段。只能返回以下之一："
            "brainstorm、planning、executing、blocked、reviewing、done。\n"
            f"任务：{state.get('task', '')}\n"
            f"当前阶段：{state.get('task_state', '')}\n"
            f"阶段产出：{json.dumps(state.get('stage_outputs', {}), ensure_ascii=False)}\n"
            f"最近记录：{json.dumps(recent, ensure_ascii=False)}\n"
            "只返回阶段单词，不要解释。"
        );
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        };
        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        );
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"));
        answer = data["choices"][0]["message"]["content"].strip().lower();
        # 大模型可能返回带前后缀的文本，这里只取第一段并清洗。
        answer = answer.split()[0].strip(".,;:!?。，；：！？") if answer else "brainstorm";
        return answer;
