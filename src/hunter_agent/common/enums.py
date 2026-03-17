from __future__ import annotations

from enum import Enum


class ProjectCategory(str, Enum):
    MANIPULATION = "manipulation"
    LEGGED_LOCOMOTION = "legged-locomotion"
    DYNAMICS_SIMULATION = "dynamics-simulation"
    MECHANICAL_DESIGN = "mechanical-design"
    EMBEDDED_SYSTEMS = "embedded-systems"
    ROBOT_CONTROL_SOFTWARE = "robot-control-software"
    HARDWARE_INDUSTRIAL_DESIGN = "hardware-industrial-design"
    PRODUCT_OPERATIONS_MARKETING = "product-operations-marketing"
    OTHER = "other"


PROJECT_CATEGORIES = [
    category.value for category in ProjectCategory if category != ProjectCategory.OTHER
]

LEGACY_PROJECT_CATEGORY_ALIASES = {
    "Manipulation绠楁硶": ProjectCategory.MANIPULATION.value,
    "Manipulation\u7b97\u6cd5": ProjectCategory.MANIPULATION.value,
    "瓒冲紡杩愬姩鎺у埗": ProjectCategory.LEGGED_LOCOMOTION.value,
    "\u8db3\u5f0f\u8fd0\u52a8\u63a7\u5236": ProjectCategory.LEGGED_LOCOMOTION.value,
    "鍔ㄥ姏瀛︿豢鐪?": ProjectCategory.DYNAMICS_SIMULATION.value,
    "\u52a8\u529b\u5b66\u4eff\u771f": ProjectCategory.DYNAMICS_SIMULATION.value,
    "鏈烘缁撴瀯璁捐": ProjectCategory.MECHANICAL_DESIGN.value,
    "\u673a\u68b0\u7ed3\u6784\u8bbe\u8ba1": ProjectCategory.MECHANICAL_DESIGN.value,
    "宓屽叆寮忚蒋纭欢": ProjectCategory.EMBEDDED_SYSTEMS.value,
    "\u5d4c\u5165\u5f0f\u8f6f\u786c\u4ef6": ProjectCategory.EMBEDDED_SYSTEMS.value,
    "鏈哄櫒浜哄簳灞傛帶鍒跺拰杞欢": ProjectCategory.ROBOT_CONTROL_SOFTWARE.value,
    "\u673a\u5668\u4eba\u5e95\u5c42\u63a7\u5236\u548c\u8f6f\u4ef6": ProjectCategory.ROBOT_CONTROL_SOFTWARE.value,
    "纭欢浜у搧澶栬璁捐": ProjectCategory.HARDWARE_INDUSTRIAL_DESIGN.value,
    "\u786c\u4ef6\u4ea7\u54c1\u5916\u89c2\u8bbe\u8ba1": ProjectCategory.HARDWARE_INDUSTRIAL_DESIGN.value,
    "鍏疯韩浜у搧杩愯惀鍜屽競鍦哄紑鍙?": ProjectCategory.PRODUCT_OPERATIONS_MARKETING.value,
    "\u5177\u8eab\u4ea7\u54c1\u8fd0\u8425\u548c\u5e02\u573a\u5f00\u53d1": ProjectCategory.PRODUCT_OPERATIONS_MARKETING.value,
    "鍏朵粬": ProjectCategory.OTHER.value,
    "\u5176\u4ed6": ProjectCategory.OTHER.value,
}
