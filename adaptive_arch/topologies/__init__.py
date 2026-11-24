from typing import Dict, Type;

from .base import BaseTopology;
from .blackboard import BlackboardTopology;
from .expert_review import ExpertReviewTopology;
from .pipeline import PipelineTopology;
from .round_table import RoundTableTopology;
from .star import StarTopology;

# 拓扑注册表：名字到类的映射，元调度器和顶层图按名字取用。
V_拓扑注册表: Dict[str, Type[BaseTopology]] = {
    RoundTableTopology.name: RoundTableTopology,
    StarTopology.name: StarTopology,
    PipelineTopology.name: PipelineTopology,
    ExpertReviewTopology.name: ExpertReviewTopology,
    BlackboardTopology.name: BlackboardTopology,
};

__all__ = [
    "BaseTopology",
    "RoundTableTopology",
    "StarTopology",
    "PipelineTopology",
    "ExpertReviewTopology",
    "BlackboardTopology",
    "V_拓扑注册表",
];
