"""
RSS Signal Collector for MarketLens 2026
Collects European market signals and performs industry clustering
Enhanced with robust error handling, retry logic, and fallback mechanisms
"""
import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
import time
import random

if TYPE_CHECKING:
    import feedparser

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    logging.warning("feedparser not available, using mock signals")

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import AgglomerativeClustering
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available, using fallback clustering")

try:
    from config import Config
except ImportError:
    # Fallback config if config.py is not available
    class Config:
        RSS_SOURCES = [
            "https://ec.europa.eu/newsroom/dae/rss.cfm",
            "https://www.eib.org/en/rss.xml",
        ]
        CLUSTERING_MIN_CLUSTERS = 5
        MAX_RETRIES = 10
        EMBEDDING_MODEL = "all-MiniLM-L6-v2"

logger = logging.getLogger(__name__)


class RSSSignalCollector:
    """
    Tool: RSS Signal Mining
    Why: Real-time European market intelligence without paid APIs
    Selection: feedparser (open-source RSS parsing)
    Enhanced with retry logic and robust error handling
    """

    def __init__(self, max_retries: int = 3, timeout: int = 10):
        self.rss_sources = Config.RSS_SOURCES
        self.max_retries = max_retries
        self.timeout = timeout
        self.request_delay = (0.5, 2.0)  # Random delay between requests

        # User agents for RSS requests
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
    
    def _fetch_rss_with_retry(self, source: str) -> Optional[Any]:
        """
        Fetch RSS feed with retry logic and error handling
        Returns feedparser.FeedParserDict or None
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching RSS from {source} (attempt {attempt + 1}/{self.max_retries})")

                # Use random user agent
                agent = random.choice(self.user_agents)

                # Parse feed with timeout
                feed = feedparser.parse(
                    source,
                    agent=agent,
                )

                # Check if feed was successfully parsed
                if hasattr(feed, 'entries') and feed.entries:
                    logger.debug(f"Successfully fetched {len(feed.entries)} entries from {source}")
                    return feed

                # Check for specific errors
                if hasattr(feed, 'bozo') and feed.bozo:
                    if hasattr(feed, 'bozo_exception'):
                        logger.warning(f"RSS parsing issue for {source}: {feed.bozo_exception}")
                    # If we have entries despite parsing issues, return the feed
                    if feed.entries:
                        logger.debug(f"Returning feed with entries despite parsing issues")
                        return feed

                logger.warning(f"No entries found in feed {source}")

                # Delay before retry
                if attempt < self.max_retries - 1:
                    delay = random.uniform(*self.request_delay) * (attempt + 1)
                    time.sleep(delay)

            except Exception as e:
                logger.warning(f"Error fetching {source} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    delay = random.uniform(*self.request_delay) * (attempt + 1)
                    time.sleep(delay)
                continue

        logger.error(f"Failed to fetch {source} after {self.max_retries} attempts")
        return None

    def collect_europe_signals(self) -> List[Dict[str, Any]]:
        """
        Collect European market signals from RSS feeds.
        Returns list of signal dictionaries.
        Enhanced with retry logic and error handling.
        """
        if not FEEDPARSER_AVAILABLE:
            logger.warning("feedparser not available, using mock signals")
            return self.get_mock_signals()

        all_signals = []
        successful_sources = 0
        failed_sources = []

        for source in self.rss_sources:
            try:
                logger.info(f"Fetching RSS from: {source}")

                # Fetch RSS with retry logic
                feed = self._fetch_rss_with_retry(source)

                if feed is None or not hasattr(feed, 'entries'):
                    failed_sources.append(source)
                    continue

                entry_count = 0
                for entry in feed.entries[:20]:  # Top 20 entries
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))

                    # Validate entry has meaningful content
                    if not title or len(title.strip()) < 10:
                        continue

                    signal = {
                        "title": title.strip(),
                        "summary": summary.strip() if summary else "",
                        "link": entry.get("link", ""),
                        "published": entry.get("published", entry.get("updated", "")),
                        "source": source,
                        "industry": self._categorize_industry(title),
                        "collected_at": datetime.now().isoformat()
                    }
                    all_signals.append(signal)
                    entry_count += 1

                if entry_count > 0:
                    successful_sources += 1
                    logger.info(f"Collected {entry_count} signals from {source}")
                else:
                    logger.warning(f"No valid signals collected from {source}")
                    failed_sources.append(source)

                # Respectful delay between sources
                time.sleep(random.uniform(*self.request_delay))

            except Exception as e:
                logger.error(f"Unexpected error fetching {source}: {e}")
                failed_sources.append(source)
                continue

        # Log summary
        logger.info(f"RSS Collection Summary: {successful_sources}/{len(self.rss_sources)} sources successful")
        if failed_sources:
            logger.warning(f"Failed sources: {', '.join(failed_sources)}")

        # Fallback to mock data if no signals collected
        if not all_signals:
            logger.warning("No signals collected from RSS, using mock data")
            return self.get_mock_signals()

        logger.info(f"✅ Collected {len(all_signals)} total signals from RSS feeds")
        return all_signals
    
    def _categorize_industry(self, title: str) -> str:
        """Categorize signal by industry based on title keywords"""
        title_lower = title.lower()
        
        industry_keywords = {
            "AI & Machine Learning": ["ai", "artificial intelligence", "machine learning", "ml"],
            "Renewable Energy": ["renewable", "solar", "wind", "energy", "green", "climate"],
            "Fintech": ["fintech", "banking", "payment", "digital finance"],
            "Healthcare Technology": ["health", "medical", "healthcare", "digital health"],
            "Electric Vehicles": ["ev", "electric vehicle", "automotive", "mobility"],
            "Cybersecurity": ["cyber", "security", "privacy", "gdpr"],
            "E-commerce": ["e-commerce", "retail", "online shopping"],
            "Manufacturing": ["manufacturing", "industry 4.0", "iot"]
        }
        
        for industry, keywords in industry_keywords.items():
            if any(kw in title_lower for kw in keywords):
                return industry
        
        return "General"
    
    def get_mock_signals(self) -> List[Dict[str, Any]]:
        """
        Provide mock signals when RSS collection fails.
        These represent realistic 2026 European market signals.
        """
        mock_signals = [
            {
                "title": "EU AI Act Enforcement Begins 2026 - €20B Compliance Market Emerges",
                "summary": "The EU AI Act enters full enforcement in 2026, creating urgent demand for AI compliance solutions across European enterprises.",
                "industry": "AI & Machine Learning",
                "source": "EU Commission",
                "published": "2026-01-15"
            },
            {
                "title": "European Renewable Energy Investment Reaches €350B in 2025",
                "summary": "EU Green Deal drives record investment in solar, wind, and energy storage solutions across member states.",
                "industry": "Renewable Energy",
                "source": "EU Commission",
                "published": "2026-01-10"
            },
            {
                "title": "PSD3 Regulations Expand Open Banking Across Europe",
                "summary": "New payment services directive drives 25% growth in fintech adoption and API-based banking solutions.",
                "industry": "Fintech",
                "source": "EU Parliament",
                "published": "2026-01-08"
            },
            {
                "title": "European Digital Health Market Grows 40% to €60B",
                "summary": "Telemedicine, health data platforms, and AI diagnostics see massive adoption post-pandemic.",
                "industry": "Healthcare Technology",
                "source": "EU Commission",
                "published": "2026-01-05"
            },
            {
                "title": "CSRD Mandates ESG Reporting for 50,000+ Companies in 2026",
                "summary": "Corporate Sustainability Reporting Directive creates €15B market for ESG data and reporting solutions.",
                "industry": "Sustainability",
                "source": "EU Commission",
                "published": "2026-01-03"
            },
            {
                "title": "European EV Sales Surge 45% Despite ICE Ban Delay",
                "summary": "Electric vehicle adoption accelerates with charging infrastructure investments exceeding €10B.",
                "industry": "Electric Vehicles",
                "source": "EU Parliament",
                "published": "2026-01-02"
            },
            {
                "title": "DORA Cybersecurity Rules Take Effect - €8B Compliance Market",
                "summary": "Digital Operational Resilience Act mandates strict cybersecurity for financial sector.",
                "industry": "Cybersecurity",
                "source": "EU Commission",
                "published": "2025-12-28"
            },
            {
                "title": "European E-commerce Cross-Border Sales Up 30%",
                "summary": "Single market digital integration drives growth in cross-border online retail and logistics.",
                "industry": "E-commerce",
                "source": "EU Parliament",
                "published": "2025-12-20"
            },
            {
                "title": "Industry 4.0 Adoption Reaches 52% in European Manufacturing",
                "summary": "IoT, automation, and AI drive productivity gains in European manufacturing sector.",
                "industry": "Manufacturing",
                "source": "EU Commission",
                "published": "2025-12-15"
            },
            {
                "title": "European Tech Startups Raise Record €45B in 2025",
                "summary": "Venture capital flows into AI, climate tech, and fintech sectors across EU member states.",
                "industry": "Technology",
                "source": "EU Parliament",
                "published": "2025-12-10"
            }
        ]
        
        # Add metadata
        for signal in mock_signals:
            signal["collected_at"] = datetime.now().isoformat()
            signal["link"] = ""
        
        logger.info(f"Using {len(mock_signals)} mock signals")
        return mock_signals


class IndustryClusteringTool:
    """
    Tool: Industry Clustering
    Why: Data-driven industry identification (not generic LLM output)
    Selection: sentence-transformers + scikit-learn (open-source ML)
    Enhanced with robust error handling and fallback mechanisms
    """

    def __init__(self):
        self.embedding_model = None
        self.min_clusters = Config.CLUSTERING_MIN_CLUSTERS
        self.max_clusters = min(Config.MAX_RETRIES, 10)  # Reasonable max
        self.model_loaded = False

        if ML_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {Config.EMBEDDING_MODEL}")
                self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
                self.model_loaded = True
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                logger.warning("Will use fallback clustering method")
                self.embedding_model = None
                self.model_loaded = False
        else:
            logger.info("ML libraries not available, using heuristic clustering")
    
    def cluster_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster signals into booming industries.
        Uses embedding-based clustering if available, otherwise heuristic.
        Enhanced with robust error handling.
        """
        if not signals:
            logger.warning("No signals to cluster, using fallback clusters")
            return self._get_fallback_clusters()

        logger.info(f"Clustering {len(signals)} signals into industries...")

        # Validate signal data
        valid_signals = [s for s in signals if s.get('title') and len(s.get('title', '').strip()) > 10]
        if len(valid_signals) < len(signals):
            logger.warning(f"Filtered out {len(signals) - len(valid_signals)} invalid signals")

        if not valid_signals:
            logger.warning("No valid signals to cluster")
            return self._get_fallback_clusters()

        # Try embedding clustering if model is available and we have enough signals
        if self.model_loaded and self.embedding_model and len(valid_signals) >= 5:
            try:
                logger.info("Using embedding-based clustering")
                result = self._embedding_clustering(valid_signals)
                if result:
                    logger.info(f"✅ Clustering complete: identified {len(result)} industries")
                    return result
                else:
                    logger.warning("Embedding clustering returned no results, using fallback")
                    return self._heuristic_clustering(valid_signals)
            except Exception as e:
                logger.error(f"Embedding clustering failed: {e}, using heuristic fallback")
                return self._heuristic_clustering(valid_signals)
        else:
            # Use heuristic clustering
            reason = "insufficient signals" if len(valid_signals) < 5 else "model not available"
            logger.info(f"Using heuristic clustering ({reason})")
            return self._heuristic_clustering(valid_signals)
    
    def _embedding_clustering(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster using sentence embeddings with robust error handling
        """
        try:
            # Prepare texts
            texts = []
            valid_signals = []
            for s in signals:
                title = s.get('title', '').strip()
                summary = s.get('summary', '').strip()
                if title:
                    texts.append(f"{title} {summary}")
                    valid_signals.append(s)

            if not texts:
                logger.warning("No valid texts for embedding clustering")
                return []

            # Generate embeddings
            logger.debug(f"Generating embeddings for {len(texts)} texts...")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

            if embeddings is None or len(embeddings) == 0:
                logger.warning("Failed to generate embeddings")
                return []

            # Determine optimal clusters
            n_clusters = min(max(self.min_clusters, len(valid_signals) // 5), self.max_clusters)
            n_clusters = min(n_clusters, len(valid_signals))  # Can't have more clusters than samples

            logger.debug(f"Clustering into {n_clusters} groups...")

            # Cluster
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='cosine',
                linkage='average'
            )
            labels = clustering.fit_predict(embeddings)

            # Group by cluster
            clusters = {}
            for i, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(valid_signals[i])

            # Convert to industry format
            industries = []
            for cluster_id, cluster_signals in clusters.items():
                if len(cluster_signals) >= 2:  # Minimum cluster size
                    industry_name = self._label_cluster(cluster_signals)
                    industries.append({
                        "industry": industry_name,
                        "signal_count": len(cluster_signals),
                        "growth_signals": [s.get("title", "")[:100] for s in cluster_signals[:5]],
                        "cluster_id": int(cluster_id)
                    })

            # Sort by signal count
            industries.sort(key=lambda x: x["signal_count"], reverse=True)

            logger.debug(f"Created {len(industries)} industry clusters")
            return industries[:10]  # Top 10 industries

        except Exception as e:
            logger.error(f"Embedding clustering error: {e}")
            return []
    
    def _heuristic_clustering(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback: Group by pre-defined industry categories
        Enhanced with validation and error handling
        """
        try:
            industry_groups = {}

            for signal in signals:
                industry = signal.get("industry", "General")
                if not industry or not isinstance(industry, str):
                    industry = "General"

                if industry not in industry_groups:
                    industry_groups[industry] = []
                industry_groups[industry].append(signal)

            # Convert to output format
            industries = []
            for name, group in industry_groups.items():
                # Include all industries with at least 1 signal
                if len(group) >= 1:
                    # Filter valid titles
                    valid_titles = [s.get("title", "")[:100] for s in group if s.get("title")]

                    industries.append({
                        "industry": name,
                        "signal_count": len(group),
                        "growth_signals": valid_titles[:5]
                    })

            # Sort by signal count
            industries.sort(key=lambda x: x["signal_count"], reverse=True)

            logger.debug(f"Heuristic clustering created {len(industries)} industry groups")

            return industries[:10]

        except Exception as e:
            logger.error(f"Heuristic clustering error: {e}")
            return self._get_fallback_clusters()
    
    def _label_cluster(self, cluster_signals: List[Dict[str, Any]]) -> str:
        """
        Label a cluster based on signal content
        Enhanced with better fallback logic
        """
        try:
            # Use most common industry label
            industries = [s.get("industry", "") for s in cluster_signals if s.get("industry")]
            if industries:
                from collections import Counter
                most_common = Counter(industries).most_common(1)
                if most_common and most_common[0][0] and most_common[0][0] != "General":
                    return most_common[0][0]

            # Fallback: extract from titles using keyword matching
            titles = " ".join([s.get("title", "").lower() for s in cluster_signals if s.get("title")])

            if not titles:
                return "Emerging Industry"

            keywords = {
                "AI & Machine Learning": ["ai", "artificial intelligence", "machine learning", "neural", "chatgpt"],
                "Renewable Energy": ["renewable", "solar", "wind", "energy", "climate", "green"],
                "Fintech": ["fintech", "banking", "payment", "blockchain", "crypto"],
                "Healthcare Technology": ["health", "medical", "healthcare", "biotech", "pharma"],
                "Cybersecurity": ["cyber", "security", "privacy", "data protection"],
                "E-commerce": ["ecommerce", "e-commerce", "retail", "online shopping"],
                "Manufacturing": ["manufacturing", "industry 4.0", "automation"],
                "Electric Vehicles": ["electric vehicle", "ev", "automotive", "battery"]
            }

            for industry, words in keywords.items():
                if any(w in titles for w in words):
                    return industry

            return "Emerging Technology"

        except Exception as e:
            logger.warning(f"Error labeling cluster: {e}")
            return "General Business"
    
    def _get_fallback_clusters(self) -> List[Dict[str, Any]]:
        """
        Fallback clusters when no signals available
        Based on known European market trends
        """
        logger.info("Using fallback industry clusters")
        return [
            {
                "industry": "AI & Machine Learning",
                "signal_count": 10,
                "growth_signals": [
                    "EU AI Act compliance requirements",
                    "Generative AI adoption in enterprises",
                    "AI-powered automation solutions"
                ]
            },
            {
                "industry": "Renewable Energy",
                "signal_count": 8,
                "growth_signals": [
                    "EU Green Deal initiatives",
                    "Solar energy investments",
                    "Wind power expansion"
                ]
            },
            {
                "industry": "Fintech",
                "signal_count": 7,
                "growth_signals": [
                    "PSD3 open banking regulations",
                    "Digital payment solutions",
                    "Blockchain applications"
                ]
            },
            {
                "industry": "Healthcare Technology",
                "signal_count": 6,
                "growth_signals": [
                    "Digital health platforms",
                    "Telemedicine services",
                    "AI diagnostics"
                ]
            },
            {
                "industry": "Cybersecurity",
                "signal_count": 5,
                "growth_signals": [
                    "DORA compliance requirements",
                    "Zero trust security",
                    "Data protection solutions"
                ]
            }
        ]
    
    def identify_booming_industries(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main entry point for industry identification
        Enhanced with validation and error handling
        """
        try:
            if not signals:
                logger.warning("No signals provided for industry identification")
                return self._get_fallback_clusters()

            logger.info(f"Identifying booming industries from {len(signals)} signals...")
            result = self.cluster_signals(signals)

            if not result:
                logger.warning("Clustering returned no results, using fallback")
                return self._get_fallback_clusters()

            return result

        except Exception as e:
            logger.error(f"Error identifying booming industries: {e}")
            return self._get_fallback_clusters()
