"""Qiitaのアカウントから記事情報を取得するモジュール"""

from typing import List, Dict, Any, Optional
import logging
import requests
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class QiitaDataFetcher:
    """Qiitaのアカウントから記事情報を取得するクラス"""

    def __init__(self, username: str):
        """
        QiitaDataFetcherの初期化

        Args:
            username: Qiitaのユーザー名
        """
        self.username = username
        self.base_url = "https://qiita.com"
        self.api_base = "https://qiita.com/api/v2"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def _validate_username(self) -> bool:
        """
        ユーザー名が有効かどうかを検証する

        Returns:
            bool: ユーザー名が有効な場合はTrue、そうでない場合はFalse
        """
        return True

    def fetch_articles_via_api(self, max_articles: int = 200) -> List[Dict[str, Any]]:
        """
        QiitaのAPIエンドポイントから記事情報を取得

        Args:
            max_articles: 取得する最大記事数（デフォルト: 200）

        Returns:
            List[Dict[str, Any]]: 記事情報のリスト
        """
        articles = []
        page = 1
        per_page = 100  # Qiita APIは最大100

        try:
            while len(articles) < max_articles:
                api_url = f"{self.api_base}/users/{self.username}/items"
                params = {"page": page, "per_page": per_page}

                logger.info(f"API経由で記事を取得中: ページ {page}")
                response = self.session.get(api_url, params=params)

                if response.status_code != 200:
                    logger.warning(f"APIの取得に失敗しました: {api_url}, ステータスコード: {response.status_code}")
                    break

                try:
                    page_articles = response.json()

                    if not page_articles:
                        logger.info("これ以上記事が見つかりません")
                        break

                    for article in page_articles:
                        if len(articles) >= max_articles:
                            break

                        tags = [tag.get("name", "") for tag in article.get("tags", [])]

                        article_data = {
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "likes": article.get("likes_count", 0),
                            "published_at": article.get("created_at", ""),
                            "description": article.get("body", "")[:200] + "...",
                            "tags": tags,
                            "guid": article.get("url", ""),
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

        return selected_articles
