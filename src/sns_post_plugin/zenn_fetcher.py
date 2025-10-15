"""Zennのアカウントから記事情報を取得するモジュール"""

from typing import List, Dict, Any, Optional
import logging
import requests
import re
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class ZennDataFetcher:
    """Zennのアカウントから記事情報を取得するクラス"""

    def __init__(self, username: str, is_company: bool = False):
        """
        ZennDataFetcherの初期化

        Args:
            username: Zennのユーザー名
            is_company: 企業アカウントかどうか
        """
        self.username = username
        self.is_company = is_company
        self.base_url = "https://zenn.dev"
        self.setup_urls()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def setup_urls(self):
        """URLを設定する"""
        if self.is_company:
            self.user_url = f"{self.base_url}/p/{self.username}"
        else:
            self.user_url = f"{self.base_url}/{self.username}"

    def _validate_username(self) -> bool:
        """
        ユーザー名が有効かどうかを検証する

        Returns:
            bool: ユーザー名が有効な場合はTrue、そうでない場合はFalse
        """
        return True

    def _fetch_tags_from_article_page(self, article_url: str) -> List[str]:
        """
        記事ページから直接タグ情報を取得する

        Args:
            article_url: 記事のURL

        Returns:
            List[str]: タグのリスト
        """
        try:
            response = self.session.get(article_url)
            if response.status_code != 200:
                return []

            topics_pattern = r'"topics":\s*\[(.*?)\]'
            topics_match = re.search(topics_pattern, response.text, re.DOTALL)

            if topics_match:
                topics_str = topics_match.group(1)
                name_pattern = r'"name":\s*"([^"]+)"'
                tag_names = re.findall(name_pattern, topics_str)
                return tag_names

        except Exception as e:
            logger.error(f"記事ページからのタグ取得中にエラーが発生しました: {e}")

        return []

    def fetch_articles_via_api(self, max_articles: int = 200) -> List[Dict[str, Any]]:
        """
        ZennのAPIエンドポイントから記事情報を取得

        Args:
            max_articles: 取得する最大記事数（デフォルト: 200）

        Returns:
            List[Dict[str, Any]]: 記事情報のリスト
        """
        articles = []
        page = 1
        per_page = 50

        try:
            while len(articles) < max_articles:
                if self.is_company:
                    api_url = f"{self.base_url}/api/articles?publication_name={self.username}&count={per_page}&page={page}"
                else:
                    api_url = f"{self.base_url}/api/articles?username={self.username}&count={per_page}&page={page}"

                logger.info(f"API経由で記事を取得中: ページ {page}")
                response = self.session.get(api_url)

                if response.status_code != 200:
                    logger.warning(f"APIの取得に失敗しました: {api_url}, ステータスコード: {response.status_code}")
                    break

                try:
                    data = response.json()
                    page_articles = data.get("articles", [])

                    if not page_articles:
                        logger.info("これ以上記事が見つかりません")
                        break

                    for article in page_articles:
                        if len(articles) >= max_articles:
                            break

                        article_url = f"{self.base_url}{article.get('path', '')}"
                        tags = [tag.get("name", "") for tag in article.get("topics", [])]

                        article_data = {
                            "title": article.get("title", ""),
                            "url": article_url,
                            "likes": article.get("liked_count", 0),
                            "published_at": article.get("published_at", ""),
                            "description": article.get("body_letters", "")[:200] + "...",
                            "tags": tags,
                            "guid": article_url,
                        }
                        articles.append(article_data)

                    page += 1

                except Exception as e:
                    logger.error(f"APIレスポンスの解析中にエラーが発生しました: {e}")
                    break

        except Exception as e:
            logger.error(f"API経由での記事取得中にエラーが発生しました: {e}")

        logger.info(f"API経由で {len(articles)} 個の記事を取得しました")
        return articles

    def fetch_articles(self, max_articles: int = 200) -> List[Dict[str, Any]]:
        """
        記事情報を取得（API経由）

        Args:
            max_articles: 取得する最大記事数（デフォルト: 200）

        Returns:
            List[Dict[str, Any]]: 記事情報のリスト
        """
        if not self._validate_username():
            logger.error(f"無効なユーザー名です: {self.username}")
            return []

        articles = self.fetch_articles_via_api(max_articles)
        return articles

    def get_popular_articles(self, limit: int = 5, random_seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        人気記事を取得する

        Args:
            limit: 取得する記事数（デフォルト: 5）
            random_seed: ランダムシードの値（Noneの場合は現在時刻を使用）

        Returns:
            List[Dict[str, Any]]: 人気記事のリスト
        """
        if random_seed is None:
            random_seed = int(datetime.now().timestamp())
        random.seed(random_seed)

        articles = self.fetch_articles()

        if not articles:
            logger.warning("記事が見つかりませんでした")
            return []

        sorted_articles = sorted(articles, key=lambda x: x.get("likes", 0), reverse=True)
        max_articles = min(100, len(sorted_articles))
        top_articles = sorted_articles[:max_articles]

        if len(top_articles) <= limit:
            return top_articles

        weights = [1.0 / (i + 1) for i in range(len(top_articles))]
        selected_articles = random.choices(population=top_articles, weights=weights, k=limit)

        for article in selected_articles:
            if not article.get("tags"):
                article["tags"] = self._fetch_tags_from_article_page(article["url"])

        return selected_articles
