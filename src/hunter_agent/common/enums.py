from __future__ import annotations

from enum import Enum


class ProjectCategory(str, Enum):
    MANIPULATION = "Manipulation算法"
    LEGGED = "足式运动控制"
    DYNAMICS_SIM = "动力学仿真"
    MECHANICAL_DESIGN = "机械结构设计"
    EMBEDDED_HW_SW = "嵌入式软硬件"
    ROBOT_LOWER_STACK = "机器人底层控制和软件"
    HARDWARE_APPEARANCE = "硬件产品外观设计"
    OPERATION_MARKETING = "具身产品运营和市场开发"
    OTHER = "其它"


PROJECT_CATEGORIES = [category.value for category in ProjectCategory]
