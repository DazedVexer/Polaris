"""
工具包入口：在应用启动时调用 register_all_tools() 批量注册所有可用工具。
"""

from tool_registry import get_tool_registry
from config import TOOLS_ENABLED


def register_all_tools():
    """注册所有可用的工具到全局注册中心"""
    registry = get_tool_registry()

    # ---- 天气工具 ----
    if TOOLS_ENABLED.get("weather", False):
        from tools.weather import WEATHER_TOOL_SCHEMA
        registry.register(**WEATHER_TOOL_SCHEMA)
        print("[Tools] ✅ 天气查询工具已注册")

    # ---- GitHub 工具 ----
    if TOOLS_ENABLED.get("github", False):
        from tools.github import GITHUB_TOOLS
        for tool in GITHUB_TOOLS:
            registry.register(**tool)
        print(f"[Tools] ✅ {len(GITHUB_TOOLS)} 个 GitHub 工具已注册")

    # ---- 文件系统工具 ----
    if TOOLS_ENABLED.get("filesystem", False):
        from tools.filesystem import FILESYSTEM_TOOLS
        for tool in FILESYSTEM_TOOLS:
            registry.register(**tool)
        print(f"[Tools] ✅ {len(FILESYSTEM_TOOLS)} 个文件系统工具已注册")

    print(f"[Tools] 总共注册 {len(registry.list_tools())} 个工具")


def get_tools_for_planner() -> str:
    """获取给 Planner 看的工具描述文本"""
    registry = get_tool_registry()
    return registry.get_tools_description()
