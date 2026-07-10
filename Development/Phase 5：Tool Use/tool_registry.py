import json
from typing import Callable, Any


class ToolRegistry:
    """
    工具注册中心。

    使用方式：
        registry = ToolRegistry()

        # 注册工具
        registry.register(
            name="get_weather",
            description="查询指定城市的天气",
            func=get_weather,
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如 Beijing"}
                },
                "required": ["city"]
            }
        )

        # 获取所有工具的 OpenAI 格式定义
        tools_schema = registry.get_openai_tools()

        # 执行工具调用
        result = registry.execute("get_weather", {"city": "Beijing"})
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}  # name → {func, schema, ...}

    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: dict,
    ):
        """注册一个新工具"""
        if name in self._tools:
            raise ValueError(f"工具 '{name}' 已注册，不允许重复。")

        self._tools[name] = {
            "name": name,
            "description": description,
            "func": func,
            "parameters": parameters,
        }

    def unregister(self, name: str):
        """注销一个工具"""
        self._tools.pop(name, None)

    def get(self, name: str) -> dict | None:
        """根据名称获取工具定义"""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名"""
        return list(self._tools.keys())

    def get_openai_tools(self) -> list[dict]:
        """
        生成 OpenAI Function Calling 格式的工具列表。
        可以直接放进 chat.completions.create(tools=...) 中。
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                }
            }
            for t in self._tools.values()
        ]

    def get_tools_description(self) -> str:
        """
        生成给 Planner 看的工具列表文本。
        Phase 4 的 Planner 不用 OpenAI tools 参数，而是把工具列表拼进 prompt。
        """
        if not self._tools:
            return "（无可用的外部工具）"

        lines = ["[可用工具列表]"]
        for name, t in self._tools.items():
            params_desc = []
            props = t["parameters"].get("properties", {})
            required = t["parameters"].get("required", [])
            for pname, pinfo in props.items():
                req_mark = "（必填）" if pname in required else "（可选）"
                params_desc.append(f"    - {pname} ({pinfo.get('type', 'string')}) {req_mark}: {pinfo.get('description', '')}")

            lines.append(f"  🔧 {name}: {t['description']}")
            lines.extend(params_desc)
        return "\n".join(lines)

    def execute(self, name: str, arguments: dict) -> str:
        """
        执行一个工具调用，返回结果字符串。

        参数:
            name: 工具名
            arguments: 参数字典（LLM 生成的 JSON 已解析为 dict）

        返回:
            工具执行结果的字符串表示
        """
        if name not in self._tools:
            return f"[错误] 未知工具：{name}"

        func = self._tools[name]["func"]
        try:
            result = func(**arguments)
            if isinstance(result, str):
                return result
            elif isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)
        except Exception as e:
            return f"[工具执行失败] {name}: {str(e)}"


# 全局单例（整个应用共用一个注册中心）
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册中心单例"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
