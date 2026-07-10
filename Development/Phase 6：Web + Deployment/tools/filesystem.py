"""
文件系统操作工具
所有操作被限制在安全根目录下，防止意外操作系统文件。
安全策略：
  - 所有路径必须解析后确认在 SAFE_ROOT 内
  - 读文件限制大小
  - 写文件不覆盖已有文件（除非显式允许）
  - 禁止操作以 . 开头的隐藏文件/目录
"""

from pathlib import Path
from config import FILESYSTEM_SAFE_ROOT, FILESYSTEM_MAX_READ_SIZE

SAFE_ROOT = Path(FILESYSTEM_SAFE_ROOT).resolve()


def _resolve_safe(file_path: str) -> Path:
    """
    解析路径并确保在安全范围内。
    如果越界，抛出 PermissionError。
    """
    target = (SAFE_ROOT / file_path).resolve()
    if not str(target).startswith(str(SAFE_ROOT)):
        raise PermissionError(f"禁止访问安全目录外的路径：{file_path}")
    return target


def read_file(file_path: str) -> str:
    """
    读取一个本地文件的内容。

    参数:
        file_path: 相对于项目根目录的文件路径，如 "kb/notes.md"

    返回:
        文件内容（字符串），最大 100KB
    """
    try:
        path = _resolve_safe(file_path)
        if not path.exists():
            return f"[错误] 文件不存在：{file_path}"
        if not path.is_file():
            return f"[错误] 不是一个文件：{file_path}"
        if path.stat().st_size > FILESYSTEM_MAX_READ_SIZE:
            return f"[错误] 文件过大（>{FILESYSTEM_MAX_READ_SIZE // 1024}KB），拒绝读取"

        content = path.read_text(encoding="utf-8")
        return content
    except PermissionError as e:
        return f"[安全限制] {e}"
    except UnicodeDecodeError:
        return f"[错误] 文件编码不是 UTF-8，无法读取：{file_path}"
    except Exception as e:
        return f"[错误] 读取文件失败：{e}"


def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    写入内容到一个文件。

    参数:
        file_path: 相对于项目根目录的文件路径
        content: 要写入的内容
        overwrite: 是否覆盖已有文件（默认 False）

    返回:
        操作结果描述
    """
    try:
        path = _resolve_safe(file_path)

        if path.exists() and not overwrite:
            return f"[错误] 文件已存在：{file_path}。如需覆盖请设置 overwrite=true"

        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding="utf-8")
        size = path.stat().st_size
        return f"文件已写入：{file_path}（{size} 字节）"
    except PermissionError as e:
        return f"[安全限制] {e}"
    except Exception as e:
        return f"[错误] 写入文件失败：{e}"


def list_directory(dir_path: str = ".") -> list[dict]:
    """
    列出目录下的文件和子目录。

    参数:
        dir_path: 相对于项目根目录的路径，默认 "." 为根目录

    返回:
        文件/目录列表，每项包含 name, type, size
    """
    try:
        path = _resolve_safe(dir_path)
        if not path.exists():
            return [{"error": f"目录不存在：{dir_path}"}]
        if not path.is_dir():
            return [{"error": f"不是一个目录：{dir_path}"}]

        items = []
        for child in sorted(path.iterdir()):
            # 跳过隐藏文件/目录
            if child.name.startswith("."):
                continue
            info = {
                "name": child.name,
                "type": "directory" if child.is_dir() else "file",
            }
            if child.is_file():
                info["size"] = child.stat().st_size
            items.append(info)

        return items
    except PermissionError as e:
        return [{"error": f"[安全限制] {e}"}]
    except Exception as e:
        return [{"error": f"列目录失败：{e}"}]


def search_files(pattern: str, dir_path: str = ".") -> list[str]:
    """
    在目录中搜索匹配的文件名（支持通配符）。

    参数:
        pattern: 文件名模式，如 "*.py" 或 "test_*"
        dir_path: 搜索的起始目录

    返回:
        匹配的文件路径列表（相对于项目根目录）
    """
    try:
        path = _resolve_safe(dir_path)
        if not path.exists() or not path.is_dir():
            return [f"[错误] 目录不存在：{dir_path}"]

        matches = []
        for child in path.rglob(pattern):
            if child.name.startswith("."):
                continue
            rel = child.relative_to(SAFE_ROOT)
            matches.append(str(rel))

        return matches
    except PermissionError as e:
        return [f"[安全限制] {e}"]
    except Exception as e:
        return [f"[错误] 搜索失败：{e}"]


# ========== 工具注册信息 ==========
FILESYSTEM_TOOLS = [
    {
        "name": "read_file",
        "description": "读取项目目录下的一个文件的内容（最大 100KB）",
        "func": read_file,
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "相对于项目根目录的文件路径，如 kb/notes.md"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "将内容写入项目目录下的一个文件（默认不覆盖已有文件）",
        "func": write_file,
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "相对于项目根目录的文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容"
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "是否覆盖已有文件，默认为 false"
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "列出项目目录下的文件和子目录",
        "func": list_directory,
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {
                    "type": "string",
                    "description": "相对于项目根目录的路径，默认为 '.'（根目录）"
                }
            },
            "required": []
        }
    },
    {
        "name": "search_files",
        "description": "在项目目录中搜索匹配模式的文件（如搜索所有 .py 文件）",
        "func": search_files,
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "文件名模式，支持通配符，如 *.py、test_*.md"
                },
                "dir_path": {
                    "type": "string",
                    "description": "搜索起始目录，默认为项目根目录"
                }
            },
            "required": ["pattern"]
        }
    },
]
