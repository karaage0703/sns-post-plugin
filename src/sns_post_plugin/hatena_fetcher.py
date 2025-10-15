"""はてなブログ記事収集・重み付けランダム選出システム"""

import requests
import json
import random
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class HatenaArchiveCrawler:
    def __init__(self, blog_url: str = "https://karaage.hatenadiary.jp", cache_file: Optional[str] = None):
        self.blog_url = blog_url

        if cache_file:
            self.cache_file = Path(cache_file)
        else:
            # デフォルトのキャッシュディレクトリ
            cache_dir = Path.home() / ".cache" / "sns-post-plugin"
            cache_dir.mkdir(parents=True, exist_ok=True)
            # ブログURLからキャッシュファイル名を生成
            blog_name = blog_url.replace("https://", "").replace("http://", "").replace("/", "_")
            self.cache_file = cache_dir / f"{blog_name}_cache.json"

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

    def generate_archive_urls(self, start_year: int = 2014, end_year: Optional[int] = None) -> List[str]:
        """月別アーカイブURLを生成"""
        if end_year is None:
            end_year = datetime.now().year

        archive_urls = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                if year == datetime.now().year and month > datetime.now().month:
                    break
                url = f"{self.blog_url}/archive/{year}/{month:02d}"
                archive_urls.append(url)
        return archive_urls

    def fetch_articles_from_archive(self, archive_url: str) -> List[Dict[str, Any]]:
        """月別アーカイブページから記事リンクを抽出"""
        try:
            response = self.session.get(archive_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            links = soup.select("a.entry-title-link")

            articles = []
            for link in links:
                title = link.text.strip()
                url = link.get("href")
                if url and title:
                    if url.startswith("/"):
                        url = self.blog_url + url

                    articles.append({"title": title, "url": url, "archive_url": archive_url})

            logger.info(f"✅ {archive_url}: {len(articles)}件の記事を取得")
            return articles

        except Exception as e:
            logger.error(f"❌ エラー {archive_url}: {e}")
            return []

    def collect_all_articles(self, start_year: int = 2014) -> List[Dict[str, Any]]:
        """全期間の記事を収集"""
        archive_urls = self.generate_archive_urls(start_year)
        all_articles = []

        logger.info(f"📚 {len(archive_urls)}個のアーカイブページをクロール開始...")

        for i, url in enumerate(archive_urls):
            articles = self.fetch_articles_from_archive(url)
            all_articles.extend(articles)

            if i % 10 == 0:
                time.sleep(1)

            if i % 50 == 0 and i > 0:
                logger.info(f"📊 進捗: {i}/{len(archive_urls)} ({len(all_articles)}件の記事を収集済み)")

        logger.info(f"🎉 収集完了: 合計{len(all_articles)}件の記事")
        return all_articles

    def get_hatena_bookmark_count(self, url: str) -> Optional[int]:
        """はてなブックマーク数を取得"""
        try:
            api_url = f"https://b.hatena.ne.jp/entry/jsonlite/?url={url}"
            response = self.session.get(api_url, timeout=10)

            if response.status_code == 200:
                response_text = response.text.strip()

                if not response_text or response_text == "null":
                    return 0

                try:
                    data = response.json()
                    if isinstance(data, dict):
                        return data.get("count", 0)
                except:
                    pass

            return None

        except Exception as e:
            if "timeout" not in str(e).lower():
                logger.error(f"⚠️ ブックマーク数取得エラー {url}: {e}")
            return None

    def _fetch_single_bookmark_count(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """単一記事のブックマーク数を取得（並列処理用）"""
        if "bookmark_count" not in article:
            bookmark_count = self.get_hatena_bookmark_count(article["url"])
            article["bookmark_count"] = bookmark_count if bookmark_count is not None else 0
        return article

    def fetch_bookmark_counts(self, articles: List[Dict[str, Any]], max_workers: int = 20) -> List[Dict[str, Any]]:
        """記事のブックマーク数を並列取得（高速化版）"""
        logger.info(f"🔖 {len(articles)}件の記事のブックマーク数を並列取得中（{max_workers}スレッド）...")
        success_count = 0
        error_count = 0
        bookmark_found_count = 0

        # 並列処理でブックマーク数を取得
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_article = {executor.submit(self._fetch_single_bookmark_count, article): article for article in articles}

            completed = 0
            for future in as_completed(future_to_article):
                try:
                    result = future.result()
                    bookmark_count = result.get("bookmark_count", 0)

                    if bookmark_count >= 0:
                        success_count += 1
                        if bookmark_count > 0:
                            bookmark_found_count += 1
                    else:
                        error_count += 1

                    completed += 1
                    if completed % 50 == 0:
                        logger.info(
                            f"📊 進捗: {completed}/{len(articles)} | 成功: {success_count}, ブックマークあり: {bookmark_found_count}"
                        )
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ ブックマーク取得エラー: {e}")

        success_rate = (success_count / len(articles)) * 100 if articles else 0
        logger.info(
            f"✅ 完了: 成功率 {success_rate:.1f}% ({success_count}/{len(articles)}) | ブックマークあり: {bookmark_found_count}件"
        )
        return articles

    def save_cache(self, articles: List[Dict[str, Any]]):
        """記事データをキャッシュファイルに保存"""
        cache_data = {"last_updated": datetime.now().isoformat(), "articles": articles}

        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 キャッシュを保存: {self.cache_file}")

    def load_cache(self) -> Optional[List[Dict[str, Any]]]:
        """キャッシュファイルから記事データを読み込み"""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            last_updated = datetime.fromisoformat(cache_data["last_updated"])
            if datetime.now() - last_updated > timedelta(days=1):
                logger.info("⏰ キャッシュが古いため更新します")
                return None

            logger.info(f"📋 キャッシュから{len(cache_data['articles'])}件の記事を読み込み")
            return cache_data["articles"]

        except Exception as e:
            logger.error(f"❌ キャッシュ読み込みエラー: {e}")
            return None

    def weighted_random_selection(self, articles: List[Dict[str, Any]], exclude_recent_days: int = 30) -> Dict[str, Any]:
        """重み付けランダム選出"""
        cutoff_date = datetime.now() - timedelta(days=exclude_recent_days)

        bookmarked_articles = [article for article in articles if article.get("bookmark_count", 0) > 0]
        no_bookmark_articles = [article for article in articles if article.get("bookmark_count", 0) == 0]

        if bookmarked_articles:
            if random.random() < 0.7 and bookmarked_articles:
                selected_articles = bookmarked_articles
                weights = [article.get("bookmark_count", 0) + 1 for article in selected_articles]
                selection_type = "ブックマーク重み付き"
            else:
                selected_articles = no_bookmark_articles if no_bookmark_articles else articles
                weights = [1 for _ in selected_articles]
                selection_type = "ランダム"
        else:
            selected_articles = articles
            weights = [1 for _ in selected_articles]
            selection_type = "全記事ランダム"

        if not selected_articles:
            selected_articles = articles
            weights = [1 for _ in selected_articles]
            selection_type = "フォールバック"

        selected_article = random.choices(selected_articles, weights=weights, k=1)[0]

        logger.info(f"🎯 選出された記事: {selected_article['title']}")
        logger.info(f"📖 ブックマーク数: {selected_article.get('bookmark_count', 0)}")
        logger.info(f"🎲 選択方法: {selection_type}")

        return selected_article

    def run_full_crawl(self, start_year: int = 2014, use_cache: bool = True) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """フルクロール実行"""
        cached_articles = self.load_cache() if use_cache else None

        if cached_articles:
            articles = cached_articles
            logger.info(f"📋 キャッシュから{len(articles)}件の記事を使用")
        else:
            articles = self.collect_all_articles(start_year=start_year)
            articles = self.fetch_bookmark_counts(articles)
            self.save_cache(articles)

        selected_article = self.weighted_random_selection(articles)

        return selected_article, articles
