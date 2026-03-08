"""
Configuration and Ollama LLM setup for MarketLens 2026
Uses LOCAL open-source LLM via Ollama (NO PAID APIs)
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class RegionConfig:
    """Region-specific configuration for data sources"""

    REGIONS = {
        "Europe": {
            "rss_sources": [
                "https://ec.europa.eu/newsroom/dae/rss.cfm",
                "https://www.eib.org/en/rss.xml",
                "https://www.eiopa.europa.eu/press-room_en/rss.xml",
            ],
            "news_sources": [
                "https://www.stateofeuropeantech.com/",
                "https://www.euractiv.com/sections/innovation-industry/",
            ],
            "fallback_rss": [
                "https://techcrunch.com/feed/",
                "https://www.wired.com/feed/rss",
            ],
            "trending_sources": [
                "https://www.stateofeuropeantech.com/",
                "https://techcrunch.com/",
            ],
            "company_discovery": [
                "https://www.crunchbase.com/hub/europe-companies",
                "https://tech.eu/companies",
            ]
        },
        "Asia": {
            "rss_sources": [
                "https://techcrunch.com/asia/feed/",
                "https://www.techinasia.com/feed",
            ],
            "news_sources": [
                "https://techcrunch.com/asia/",
                "https://www.techinasia.com/",
            ],
            "fallback_rss": [
                "https://techcrunch.com/feed/",
                "https://www.wired.com/feed/rss",
            ],
            "trending_sources": [
                "https://techcrunch.com/asia/",
                "https://www.techinasia.com/",
            ],
            "company_discovery": [
                "https://www.crunchbase.com/hub/asia-companies",
            ]
        },
        "United States": {
            "rss_sources": [
                "https://techcrunch.com/feed/",
                "https://www.wired.com/feed/rss",
            ],
            "news_sources": [
                "https://techcrunch.com/",
                "https://www.theverge.com/",
            ],
            "fallback_rss": [
                "https://feeds.feedburner.com/venturebeat/SZYF",
                "https://www.entrepreneur.com/latest.rss",
            ],
            "trending_sources": [
                "https://techcrunch.com/",
                "https://www.theverge.com/",
            ],
            "company_discovery": [
                "https://www.crunchbase.com/hub/united-states-companies",
            ]
        },
        "China": {
            "rss_sources": [
                "https://technode.com/feed/",
            ],
            "news_sources": [
                "https://technode.com/",
            ],
            "fallback_rss": [
                "https://techcrunch.com/asia/feed/",
            ],
            "trending_sources": [
                "https://technode.com/",
            ],
            "company_discovery": [
                "https://www.crunchbase.com/hub/china-companies",
            ]
        }
    }

    @classmethod
    def get_config(cls, region: str) -> dict:
        """
        Get region-specific configuration

        Args:
            region: Region name (e.g., "Europe", "Asia", "United States", "China")

        Returns:
            Dictionary with region-specific data sources
        """
        # Normalize region name (handle case variations)
        region_normalized = region.strip()

        # Try exact match first
        if region_normalized in cls.REGIONS:
            return cls.REGIONS[region_normalized]

        # Try case-insensitive match
        for key in cls.REGIONS:
            if key.lower() == region_normalized.lower():
                return cls.REGIONS[key]

        # Default to Europe if region not found
        logger.warning(f"Region '{region}' not found, defaulting to Europe")
        return cls.REGIONS["Europe"]

    @classmethod
    def get_available_regions(cls) -> list:
        """Get list of available regions"""
        return list(cls.REGIONS.keys())


class Config:
    """System configuration"""

    # Ollama Configuration (LOCAL, FREE, OPEN-SOURCE)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # Can use llama3.2, mistral, etc.
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
    OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "4000"))

    # Default settings
    DEFAULT_REGION = "Europe"

    # Scraping Configuration
    REQUEST_DELAY = int(os.getenv("REQUEST_DELAY", "1"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT = int(os.getenv("TIMEOUT", "900"))
    USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    # RSS Sources (DEPRECATED - Use RegionConfig.get_config(region) instead)
    RSS_SOURCES = [
        "https://ec.europa.eu/newsroom/api/rss",
        "https://www.europarl.europa.eu/rss/doc/top-stories/en.xml"
    ]

    # Clustering Configuration
    CLUSTERING_MIN_CLUSTERS = 5
    CLUSTERING_MAX_CLUSTERS = 10
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_ollama_llm(temperature: float = None):
    """
    Initialize Ollama LLM (LOCAL, FREE, OPEN-SOURCE)
    No paid APIs - runs locally on your machine
    Requires Ollama to be installed and running
    """
    from langchain.llms.base import LLM
    from typing import Optional, List, Any
    import requests

    temp = temperature if temperature is not None else Config.OLLAMA_TEMPERATURE

    # Create custom LLM class for Ollama
    class OllamaLLM(LLM):
        """Custom LangChain LLM wrapper for Ollama (local, open-source)"""

        base_url: str = Config.OLLAMA_BASE_URL
        model: str = Config.OLLAMA_MODEL
        temperature: float = 0.2
        max_tokens: int = 4000

        @property
        def _llm_type(self) -> str:
            return "ollama"

        def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
            """Execute LLM call using Ollama API"""
            try:
                # Call Ollama API
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": self.max_tokens
                        }
                    },
                    timeout=900
                )
                response.raise_for_status()

                result = response.json()
                return result.get('response', '')

            except requests.exceptions.ConnectionError:
                error_msg = (
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Please ensure Ollama is installed and running:\n"
                    "1. Install: https://ollama.ai/download\n"
                    "2. Start: ollama serve\n"
                    f"3. Pull model: ollama pull {self.model}"
                )
                logger.error(error_msg)
                raise ConnectionError(error_msg)
            except Exception as e:
                logger.error(f"Ollama API call failed: {e}")
                raise

    logger.info(f"Using LOCAL Ollama LLM: {Config.OLLAMA_MODEL} (FREE, OPEN-SOURCE)")
    return OllamaLLM(temperature=temp, max_tokens=Config.OLLAMA_MAX_TOKENS)


# Backward compatibility alias
def get_groq_llm(temperature: float = None):
    """
    Backward compatibility - now uses Ollama instead of Groq
    """
    logger.warning("get_groq_llm() is deprecated. Using local Ollama instead of paid Groq API")
    return get_ollama_llm(temperature)
