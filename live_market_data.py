"""
Live Market Data Collector for MarketLens 2026
Gathers real-time market signals from multiple sources for any region
NO HARDCODED DATA - All data is live from the internet
Enhanced with robust error handling and anti-blocking measures
Region-agnostic design supports Europe, Asia, United States, China, and more
"""
import logging
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
import time
import re
import random
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class LiveMarketDataCollector:
    """
    Collects live market data from real sources for any region
    NO HARDCODED DATA - Everything is scraped live
    Enhanced with retry logic, rotating user agents, and fallback mechanisms
    Region-agnostic design supports global market intelligence
    """

    def __init__(self, region: str = "Europe", max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Initialize collector with region-specific data sources

        Args:
            region: Target region (e.g., "Europe", "Asia", "United States", "China")
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff factor for retries
        """
        # Import RegionConfig here to avoid circular imports
        from config import RegionConfig

        self.region = region
        self.region_config = RegionConfig.get_config(region)

        # Create session with retry strategy
        self.session = requests.Session()

        # Configure retry strategy for transient errors
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Rotating user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

        # Set initial headers
        self._update_headers()

        # Load region-specific data sources
        self.rss_sources = self.region_config.get("rss_sources", [])
        self.news_sources = self.region_config.get("news_sources", [])
        self.fallback_rss_sources = self.region_config.get("fallback_rss", [])
        self.trending_sources = self.region_config.get("trending_sources", [])

        self.max_retries = max_retries
        self.request_delay = (1, 3)  # Random delay between 1-3 seconds

        logger.info(f"LiveMarketDataCollector initialized for region: {region}")

    def _update_headers(self):
        """Update session headers with a random user agent"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        })

    def _safe_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Make a safe HTTP request with retry logic and error handling"""
        for attempt in range(self.max_retries):
            try:
                # Rotate user agent for each retry
                self._update_headers()

                response = self.session.get(url, timeout=timeout, allow_redirects=True)

                # Check for successful response
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden for {url} (attempt {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(random.uniform(2, 5))  # Longer delay for 403
                elif response.status_code == 429:
                    logger.warning(f"Rate limited for {url}, backing off...")
                    time.sleep(random.uniform(5, 10))
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {url} (attempt {attempt + 1}/{self.max_retries})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for {url} (attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logger.warning(f"Unexpected error for {url}: {e}")

            # Random delay before retry
            if attempt < self.max_retries - 1:
                time.sleep(random.uniform(*self.request_delay))

        return None

    def get_live_market_signals(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Gather LIVE market signals from real sources for configured region
        NO HARDCODED DATA
        Enhanced with robust error handling and fallback mechanisms

        Args:
            limit: Maximum number of signals to return

        Returns:
            List of market signal dictionaries
        """
        logger.info(f"🌐 Gathering LIVE {self.region} market signals from internet...")

        signals = []

        # 1. Collect from RSS feeds (most reliable)
        try:
            rss_signals = self._collect_rss_signals()
            signals.extend(rss_signals)
            logger.info(f"   ✓ Collected {len(rss_signals)} signals from RSS feeds")
        except Exception as e:
            logger.error(f"RSS collection failed: {e}")

        # 2. Scrape news websites (may fail due to blocking)
        try:
            news_signals = self._scrape_news_sites()
            signals.extend(news_signals)
            logger.info(f"   ✓ Scraped {len(news_signals)} signals from news sites")
        except Exception as e:
            logger.error(f"News scraping failed: {e}")

        # 3. Get trending topics (additional sources)
        try:
            trending = self._get_trending_topics()
            signals.extend(trending)
            logger.info(f"   ✓ Found {len(trending)} trending topics")
        except Exception as e:
            logger.error(f"Trending topics collection failed: {e}")

        # Check if we have enough signals
        if len(signals) < 5:
            logger.warning(f"Only collected {len(signals)} signals - data collection may be impaired")

        # Deduplicate and limit
        unique_signals = self._deduplicate_signals(signals)
        logger.info(f"✅ Total unique signals: {len(unique_signals)}")

        if not unique_signals:
            logger.error("⚠️ No signals collected - all sources may be unavailable or blocking")
            return []

        return unique_signals[:limit]

    def _collect_rss_signals(self) -> List[Dict[str, Any]]:
        """Collect signals from RSS feeds with retry logic"""
        signals = []
        all_sources = self.rss_sources + self.fallback_rss_sources

        for rss_url in all_sources:
            try:
                logger.debug(f"Fetching RSS: {rss_url}")

                # Try to fetch RSS feed with timeout and user agent
                feed = feedparser.parse(
                    rss_url,
                    agent=random.choice(self.user_agents)
                )

                # Check if feed was successfully parsed
                if not hasattr(feed, 'entries') or not feed.entries:
                    logger.warning(f"No entries found in RSS feed: {rss_url}")
                    continue

                if feed.get('bozo', 0) == 1 and feed.entries:
                    logger.debug(f"RSS feed has parsing issues but has entries: {rss_url}")

                entry_count = 0
                for entry in feed.entries[:10]:  # Top 10 from each source
                    title = entry.get('title', '')
                    summary = entry.get('summary', entry.get('description', ''))

                    if title and len(title.strip()) > 10:
                        # Extract industry from content
                        industry = self._extract_industry_from_text(title + " " + summary)

                        signals.append({
                            'industry': industry,
                            'title': title[:200],
                            'source': 'RSS',
                            'date': entry.get('published', datetime.now().isoformat()),
                            'url': rss_url
                        })
                        entry_count += 1

                logger.debug(f"Collected {entry_count} signals from {rss_url}")

                # Respectful delay between requests
                time.sleep(random.uniform(*self.request_delay))

            except Exception as e:
                logger.warning(f"Failed to fetch RSS {rss_url}: {e}")
                continue

        return signals

    def _scrape_news_sites(self) -> List[Dict[str, Any]]:
        """Scrape tech and business news sites with robust error handling"""
        signals = []
        successful_scrapes = 0

        for news_url in self.news_sources:
            try:
                logger.debug(f"Scraping: {news_url}")

                # Use safe request method with retry logic
                response = self._safe_request(news_url, timeout=15)

                if response is None:
                    logger.warning(f"Failed to scrape {news_url} after {self.max_retries} attempts - skipping")
                    continue

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Try multiple selectors to find article headlines
                headline_selectors = [
                    {'tags': ['h2', 'h3', 'h4'], 'class': None},
                    {'tags': ['article'], 'class': None},
                    {'tags': ['div'], 'class': ['article', 'post', 'entry']},
                ]

                headlines = []
                for selector in headline_selectors:
                    if selector['class']:
                        for tag in selector['tags']:
                            headlines.extend(soup.find_all(tag, class_=selector['class'], limit=20))
                    else:
                        headlines.extend(soup.find_all(selector['tags'], limit=20))

                    if headlines:
                        break

                article_count = 0
                for headline in headlines:
                    title = headline.get_text().strip()

                    # Clean up title
                    title = re.sub(r'\s+', ' ', title)  # Remove extra whitespace
                    title = title.replace('\n', ' ').replace('\r', '')

                    if len(title) > 20 and len(title) < 300:  # Filter reasonable lengths
                        industry = self._extract_industry_from_text(title)

                        signals.append({
                            'industry': industry,
                            'title': title[:200],
                            'source': 'News Scraping',
                            'date': datetime.now().isoformat(),
                            'url': news_url
                        })
                        article_count += 1

                if article_count > 0:
                    successful_scrapes += 1
                    logger.debug(f"Scraped {article_count} articles from {news_url}")
                else:
                    logger.warning(f"No valid articles found at {news_url}")

                # Respectful delay between requests
                time.sleep(random.uniform(*self.request_delay))

            except Exception as e:
                logger.warning(f"Unexpected error scraping {news_url}: {e}")
                continue

        logger.info(f"Successfully scraped {successful_scrapes}/{len(self.news_sources)} news sources")
        return signals

    def _get_trending_topics(self) -> List[Dict[str, Any]]:
        """
        Get trending business topics from search trends and news aggregators
        Uses region-specific trending sources
        """
        signals = []

        # Use region-specific trending sources
        for url in self.trending_sources:
            try:
                logger.debug(f"Fetching trending topics from: {url}")
                response = self._safe_request(url, timeout=15)

                if response is None:
                    logger.warning(f"Failed to fetch trending topics from {url}")
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                articles = soup.find_all(['h2', 'h3', 'h1'], limit=15)

                topic_count = 0
                for article in articles:
                    title = article.get_text().strip()
                    title = re.sub(r'\s+', ' ', title)  # Clean whitespace

                    if len(title) > 20 and len(title) < 300:
                        industry = self._extract_industry_from_text(title)
                        signals.append({
                            'industry': industry,
                            'title': title[:200],
                            'source': 'Trending Topics',
                            'date': datetime.now().isoformat(),
                            'url': url
                        })
                        topic_count += 1

                logger.debug(f"Found {topic_count} trending topics from {url}")

                # Respectful delay
                time.sleep(random.uniform(*self.request_delay))

            except Exception as e:
                logger.warning(f"Failed to get trending topics from {url}: {e}")
                continue

        return signals

    def _extract_industry_from_text(self, text: str) -> str:
        """
        Extract industry/sector from text using keyword matching
        """
        text_lower = text.lower()

        # Industry keyword mapping
        industry_keywords = {
            'AI & Machine Learning': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning'],
            'Renewable Energy': ['renewable', 'solar', 'wind energy', 'green energy', 'clean energy', 'climate'],
            'Healthcare Technology': ['healthcare', 'health tech', 'medical', 'biotech', 'pharma'],
            'Electric Vehicles': ['electric vehicle', 'ev', 'automotive', 'tesla', 'battery'],
            'Cybersecurity': ['cybersecurity', 'security', 'cyber', 'data protection'],
            'Fintech': ['fintech', 'banking', 'payment', 'blockchain', 'crypto', 'finance'],
            'Manufacturing': ['manufacturing', 'industry 4.0', 'automation', 'robotics'],
            'E-commerce': ['e-commerce', 'ecommerce', 'retail', 'shopping'],
            'Cloud Computing': ['cloud', 'saas', 'paas', 'infrastructure'],
            'Biotechnology': ['biotech', 'genomics', 'life sciences'],
            'Smart Cities': ['smart city', 'iot', 'urban', 'smart infrastructure'],
            'EdTech': ['edtech', 'education', 'learning', 'training'],
            'AgriTech': ['agritech', 'agriculture', 'farming', 'food tech'],
            'Space Technology': ['space', 'satellite', 'aerospace'],
            'Logistics': ['logistics', 'supply chain', 'delivery', 'warehousing'],
            'Green Technology': ['green tech', 'sustainability', 'circular economy'],
            '5G Infrastructure': ['5g', 'telecom', 'network'],
            'Data Analytics': ['data analytics', 'big data', 'analytics'],
            'Digital Transformation': ['digital transformation', 'digitalization'],
        }

        for industry, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return industry

        return 'General Business'

    def _deduplicate_signals(self, signals: List[Dict]) -> List[Dict]:
        """Remove duplicate signals based on title similarity"""
        unique_signals = []
        seen_titles = set()

        for signal in signals:
            title = signal.get('title', '').lower().strip()
            # Create a simplified version for comparison
            title_key = re.sub(r'\W+', '', title)[:50]

            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_signals.append(signal)

        return unique_signals

    def get_live_europe_market_signals(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Backward compatibility wrapper for get_live_market_signals
        DEPRECATED: Use get_live_market_signals() instead
        """
        logger.warning("get_live_europe_market_signals() is deprecated. Use get_live_market_signals() instead")
        return self.get_live_market_signals(limit=limit)

    def analyze_booming_industries(self, signals: List[Dict]) -> List[Dict[str, Any]]:
        """
        Analyze signals to identify booming industries
        Based on LIVE data, not hardcoded
        """
        logger.info("📊 Analyzing booming industries from live signals...")

        # Count signal frequency by industry
        industry_counts = {}
        industry_signals = {}

        for signal in signals:
            industry = signal.get('industry', 'General Business')

            if industry not in industry_counts:
                industry_counts[industry] = 0
                industry_signals[industry] = []

            industry_counts[industry] += 1
            industry_signals[industry].append(signal.get('title', ''))

        # Sort industries by frequency (most mentioned = most booming)
        sorted_industries = sorted(
            industry_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Create booming industries list
        booming_industries = []

        for industry, count in sorted_industries[:10]:  # Top 10 industries
            booming_industries.append({
                'industry': industry,
                'growth_signals': industry_signals[industry][:5],  # Top 5 signals
                'signal_count': count,
                'why_booming': f"Based on {count} recent market signals and news mentions",
                'data_source': 'Live market intelligence',
                'analysis_date': datetime.now().isoformat()
            })

        logger.info(f"✅ Identified {len(booming_industries)} booming industries from live data")
        return booming_industries

    def get_industry_trends(self, signals: List[Dict]) -> Dict[str, Any]:
        """
        Extract industry trends from live signals
        NO HARDCODED DATA
        """
        logger.info("📈 Extracting industry trends from live data...")

        # Analyze growth indicators from signals
        growth_indicators = []
        tech_trends = []
        regulatory_trends = []

        for signal in signals:
            title = signal.get('title', '').lower()
            industry = signal.get('industry', '')

            # Detect growth mentions
            if any(word in title for word in ['growth', 'growing', 'expanding', 'increase', 'surge']):
                growth_indicators.append({
                    'industry': industry,
                    'signal': signal.get('title', '')[:100],
                    'source': signal.get('source', 'Unknown'),
                    'date': signal.get('date', '')
                })

            # Detect technology trends
            if any(word in title for word in ['technology', 'innovation', 'digital', 'adoption']):
                tech_trends.append({
                    'technology': industry,
                    'trend': signal.get('title', '')[:100],
                    'source': signal.get('source', 'Unknown')
                })

            # Detect regulatory changes
            if any(word in title for word in ['regulation', 'policy', 'law', 'compliance', 'act']):
                regulatory_trends.append({
                    'regulation': signal.get('title', '')[:80],
                    'impact': f"Emerging trend in {industry}",
                    'source': signal.get('source', 'Unknown')
                })

        trends = {
            'industry_growth_indicators': growth_indicators[:10],
            'technology_trends': tech_trends[:10],
            'regulatory_changes': regulatory_trends[:8],
            'data_source': 'Live market intelligence',
            'analysis_date': datetime.now().isoformat()
        }

        logger.info(f"✅ Extracted trends: {len(growth_indicators)} growth, {len(tech_trends)} tech, {len(regulatory_trends)} regulatory")
        return trends


# Convenience function
def get_live_market_intelligence(region: str = "Europe", limit: int = 30) -> Dict[str, Any]:
    """
    Get complete live market intelligence for any region (no hardcoded data)

    Args:
        region: Target region (e.g., "Europe", "Asia", "United States", "China")
        limit: Maximum number of signals to collect

    Returns:
        dict with 'signals', 'booming_industries', 'trends', 'region'
    """
    collector = LiveMarketDataCollector(region=region)

    # Collect live signals
    signals = collector.get_live_market_signals(limit=limit)

    # Analyze industries
    booming_industries = collector.analyze_booming_industries(signals)

    # Extract trends
    trends = collector.get_industry_trends(signals)

    return {
        'region': region,
        'signals': signals,
        'booming_industries': booming_industries,
        'trends': trends,
        'timestamp': datetime.now().isoformat(),
        'data_source': f'Live {region} market intelligence - NO HARDCODED DATA'
    }


if __name__ == "__main__":
    # Test the collector with multiple regions
    import sys
    logging.basicConfig(level=logging.INFO)

    # Get region from command line or default to Europe
    test_region = sys.argv[1] if len(sys.argv) > 1 else "Europe"

    print(f"Testing Live Market Data Collector for {test_region}...")
    print("=" * 60)

    data = get_live_market_intelligence(region=test_region, limit=20)

    print(f"\n✅ Region: {data['region']}")
    print(f"✅ Collected {len(data['signals'])} live market signals")
    print(f"✅ Identified {len(data['booming_industries'])} booming industries")
    print(f"✅ Extracted {len(data['trends']['industry_growth_indicators'])} growth indicators")
    print(f"\nTop 5 Booming Industries in {test_region} (from LIVE data):")
    for i, ind in enumerate(data['booming_industries'][:5], 1):
        print(f"  {i}. {ind['industry']} - {ind['signal_count']} signals")
    print("\nTest with different regions:")
    print("  python live_market_data.py Europe")
    print("  python live_market_data.py Asia")
    print("  python live_market_data.py 'United States'")
    print("  python live_market_data.py China")
