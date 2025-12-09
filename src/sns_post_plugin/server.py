"""SNS Post Plugin MCP Server

Zenn、Qiita、はてなブログの記事を取得するためのMCPサーバー
"""

import json
import logging
from typing import Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from .zenn_fetcher import ZennDataFetcher
from .hatena_fetcher import HatenaArchiveCrawler
from .qiita_fetcher import QiitaDataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("sns-post-plugin")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """利用可能なツールのリストを返す"""
    return [
        types.Tool(
            name="fetch_zenn_articles",
            description="Zennの記事を取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Zennのユーザー名",
                    },
                    "is_company": {
                        "type": "boolean",
                        "description": "企業アカウント（/p/username）の場合はtrue",
                        "default": False,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得する記事数",
                        "default": 1,
                    },
                    "random_seed": {
                        "type": "integer",
                        "description": "ランダムシード（再現性のため）",
                    },
                },
                "required": ["username"],
            },
        ),
        types.Tool(
            name="fetch_hatena_articles",
            description="はてなブログの記事を取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "blog_url": {
                        "type": "string",
                        "description": "はてなブログのURL",
                    },
                    "start_year": {
                        "type": "integer",
                        "description": "記事収集の開始年",
                        "default": 2014,
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "キャッシュを使用するか",
                        "default": True,
                    },
                },
                "required": ["blog_url"],
            },
        ),
        types.Tool(
            name="fetch_qiita_articles",
            description="Qiitaの記事を取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Qiitaのユーザー名",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "取得する記事数",
                        "default": 1,
                    },
                    "random_seed": {
                        "type": "integer",
                        "description": "ランダムシード（再現性のため）",
                    },
                },
                "required": ["username"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """ツールの実行を処理"""
    if not arguments:
        raise ValueError("Arguments are required")

    if name == "fetch_zenn_articles":
        username = arguments.get("username")
        if not username:
            raise ValueError("username is required")

        is_company = arguments.get("is_company", False)
        limit = arguments.get("limit", 1)
        random_seed = arguments.get("random_seed")

        try:
            fetcher = ZennDataFetcher(username, is_company=is_company)
            articles = fetcher.get_popular_articles(limit=limit, random_seed=random_seed)

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(articles, ensure_ascii=False, indent=2),
                )
            ]
        except Exception as e:
            logger.error(f"Zenn記事の取得中にエラーが発生しました: {e}")
            raise

    elif name == "fetch_hatena_articles":
        blog_url = arguments.get("blog_url")
        if not blog_url:
            raise ValueError("blog_url is required")

        start_year = arguments.get("start_year", 2014)
        use_cache = arguments.get("use_cache", True)

        try:
            crawler = HatenaArchiveCrawler(blog_url=blog_url)
            selected_article, _ = crawler.run_full_crawl(start_year=start_year, use_cache=use_cache)

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(selected_article, ensure_ascii=False, indent=2),
                )
            ]
        except Exception as e:
            logger.error(f"はてなブログ記事の取得中にエラーが発生しました: {e}")
            raise

    elif name == "fetch_qiita_articles":
        username = arguments.get("username")
        if not username:
            raise ValueError("username is required")

        limit = arguments.get("limit", 1)
        random_seed = arguments.get("random_seed")

        try:
            fetcher = QiitaDataFetcher(username)
            articles = fetcher.get_popular_articles(limit=limit, random_seed=random_seed)

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(articles, ensure_ascii=False, indent=2),
                )
            ]
        except Exception as e:
            logger.error(f"Qiita記事の取得中にエラーが発生しました: {e}")
            raise

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """MCPサーバーのメインエントリーポイント"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sns-post-plugin",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run():
    """同期的なエントリーポイント（CLIから呼ばれる）"""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run()
