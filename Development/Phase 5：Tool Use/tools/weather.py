"""
天气查询工具
依赖：OpenWeatherMap API（免费层 1000 次/天）
注册：https://openweathermap.org/api
"""

import requests
from config import OPENWEATHER_API_KEY


def get_weather(city: str) -> dict:
    """
    查询指定城市的当前天气。

    参数:
        city: 城市名（英文或中文，如 Beijing、北京）

    返回:
        {
            "city": "Beijing",
            "temperature": 28.5,
            "feels_like": 30.1,
            "humidity": 65,
            "description": "晴，少云",
            "wind_speed": 3.2
        }
    """
    if not OPENWEATHER_API_KEY:
        return {"error": "天气服务未配置 API Key，请在 .env 中设置 OPENWEATHER_API_KEY"}

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "zh_cn",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return {
            "city": data.get("name", city),
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": data.get("wind", {}).get("speed", 0),
        }
    except requests.exceptions.Timeout:
        return {"error": f"请求超时：无法连接到天气服务"}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"未找到城市：{city}"}
        return {"error": f"天气 API 错误：{e.response.status_code}"}
    except Exception as e:
        return {"error": f"天气查询失败：{str(e)}"}


WEATHER_TOOL_SCHEMA = {
    "name": "get_weather",
    "description": "查询指定城市的当前天气（温度、湿度、风速、天气描述）",
    "func": get_weather,
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名，支持中英文，如 Beijing、北京、Tokyo"
            }
        },
        "required": ["city"]
    }
}
