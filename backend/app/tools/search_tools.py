"""
搜索工具模块
用于调用搜索引擎和抓取网页内容
"""

from typing import List, Dict, Any

from app.core.config import settings


def serpapi_search(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    调用SerpAPI搜索，返回结构化结果列表

    Args:
        query: 搜索关键词
        num_results: 返回结果数量

    Returns:
        结果列表，每项含 title / link / snippet
    """
    from serpapi import GoogleSearch

    params = {
        "q": query,
        "num": num_results,
        "api_key": settings.SERPAPI_KEY,
        "engine": "google",
        "hl": "zh-cn",
        "gl": "cn",
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "organic_results" not in results:
        return []

    formatted_results = []
    for result in results["organic_results"][:num_results]:
        formatted_results.append({
            "title": result.get("title", ""),
            "link": result.get("link", ""),
            "snippet": result.get("snippet", ""),
        })

    return formatted_results
