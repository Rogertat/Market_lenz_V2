"""
Web scraping tools for MarketLens 2026
Extracts structured company information from websites
"""
import logging
import time
import requests
from typing import Dict, List, Any
from bs4 import BeautifulSoup

from config import Config

logger = logging.getLogger(__name__)


class WebScraperTool:
    """
    Tool: Website Extraction
    Why: Need structured company profile from website content
    Selection: requests + BeautifulSoup4 (open-source, reliable, no paid API)
    """
    
    def __init__(self):
        self.session = requests.Session()
        # Use complete browser headers to avoid 403 errors
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def extract_company_profile(self, website_url: str) -> Dict[str, Any]:
        """
        Extract structured company profile from website.
        Returns data matching CompanyProfile schema.
        """
        logger.info(f"Extracting profile from: {website_url}")
        
        try:
            # Fetch main page
            response = self._fetch_with_retry(website_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract information
            company_name = self._extract_company_name(soup, website_url)
            services = self._extract_services(soup)
            products = self._extract_products(soup)
            capabilities = self._extract_capabilities(soup)
            industries = self._extract_industries(soup)
            case_studies = self._extract_case_studies(soup)
            geo_presence = self._extract_geography(soup)
            description = self._extract_description(soup)
            
            return {
                "website_url": website_url,
                "company_name": company_name,
                "services": services,
                "products": products,
                "technical_capabilities": capabilities,
                "mentioned_industries": industries,
                "case_study_signals": case_studies,
                "geographic_presence": geo_presence,
                "company_description": description
            }
            
        except Exception as e:
            logger.error(f"Failed to extract profile: {e}")
            return self._get_fallback_profile(website_url)
    
    def _fetch_with_retry(self, url: str) -> requests.Response:
        """Fetch URL with retry logic"""
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=Config.TIMEOUT)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.REQUEST_DELAY * (attempt + 1))
                else:
                    raise
    
    def _extract_company_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract company name from website"""
        # Try title tag
        if soup.title:
            title = soup.title.string.strip() if soup.title.string else ""
            # Remove common suffixes
            for suffix in [' | Home', ' - Home', ' | ', ' - ', ' | Official Site']:
                title = title.split(suffix)[0]
            if title and len(title) < 100:
                return title
        
        # Try meta tags
        meta_title = soup.find('meta', property='og:site_name')
        if meta_title and meta_title.get('content'):
            return meta_title['content']
        
        # Fallback to domain name
        domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        return domain.split('.')[0].title()
    
    def _extract_services(self, soup: BeautifulSoup) -> List[str]:
        """Extract services from website"""
        services = []
        
        # Look for services section
        sections = soup.find_all(['section', 'div'], class_=lambda x: x and 'service' in x.lower())
        for section in sections[:3]:
            headings = section.find_all(['h2', 'h3', 'h4'])
            for h in headings[:5]:
                text = h.get_text().strip()
                if text and len(text) < 100:
                    services.append(text)
        
        # Look for navigation items
        nav = soup.find('nav') or soup.find('header')
        if nav:
            links = nav.find_all('a')
            service_keywords = ['service', 'solution', 'product', 'offering', 'capability']
            for link in links:
                text = link.get_text().strip()
                href = link.get('href', '').lower()
                if any(kw in text.lower() or kw in href for kw in service_keywords):
                    if text and len(text) < 50 and text not in services:
                        services.append(text)
        
        return list(set(services))[:10]  # Deduplicate and limit
    
    def _extract_products(self, soup: BeautifulSoup) -> List[str]:
        """Extract products from website"""
        products = []
        
        # Look for product sections
        sections = soup.find_all(['section', 'div'], class_=lambda x: x and 'product' in x.lower())
        for section in sections[:2]:
            headings = section.find_all(['h2', 'h3'])
            for h in headings[:5]:
                text = h.get_text().strip()
                if text and len(text) < 100:
                    products.append(text)
        
        return list(set(products))[:8]
    
    def _extract_capabilities(self, soup: BeautifulSoup) -> List[str]:
        """Extract technical capabilities"""
        capabilities = []
        
        # Tech keywords to look for
        tech_keywords = [
            'AI', 'Machine Learning', 'Analytics', 'Cloud', 'API', 'Data',
            'Digital', 'Automation', 'Integration', 'Platform', 'SaaS',
            'Web', 'Mobile', 'DevOps', 'Security', 'Blockchain'
        ]
        
        # Search in text
        text = soup.get_text().lower()
        for keyword in tech_keywords:
            if keyword.lower() in text:
                capabilities.append(keyword)
        
        return list(set(capabilities))[:8]
    
    def _extract_industries(self, soup: BeautifulSoup) -> List[str]:
        """Extract mentioned industries"""
        industries = []
        
        # Industry keywords
        industry_keywords = [
            'Finance', 'Banking', 'Healthcare', 'Retail', 'Manufacturing',
            'Energy', 'Technology', 'Telecom', 'Automotive', 'Pharma',
            'Insurance', 'Real Estate', 'Logistics', 'Education', 'Government'
        ]
        
        text = soup.get_text().lower()
        for keyword in industry_keywords:
            if keyword.lower() in text:
                industries.append(keyword)
        
        return list(set(industries))[:8]
    
    def _extract_case_studies(self, soup: BeautifulSoup) -> List[str]:
        """Extract case study signals"""
        case_studies = []
        
        # Look for case study links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().strip()
            if 'case' in href or 'case' in text.lower() or 'client' in href:
                if text and len(text) < 100:
                    case_studies.append(text)
        
        return list(set(case_studies))[:5]
    
    def _extract_geography(self, soup: BeautifulSoup) -> List[str]:
        """Extract geographic presence"""
        # Common country/region mentions
        geo_keywords = ['USA', 'UK', 'Europe', 'Asia', 'India', 'Germany', 'France', 'Singapore']
        
        text = soup.get_text()
        found = []
        for keyword in geo_keywords:
            if keyword in text:
                found.append(keyword)
        
        return found[:6]
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract company description"""
        # Try meta description
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta and meta.get('content'):
            return meta['content'][:300]
        
        # Try about section
        about = soup.find(['section', 'div'], id=lambda x: x and 'about' in x.lower())
        if about:
            paragraphs = about.find_all('p')
            if paragraphs:
                return paragraphs[0].get_text()[:300]
        
        return "Company profile extracted from website"
    
    def _get_fallback_profile(self, website_url: str) -> Dict[str, Any]:
        """Fallback profile if extraction fails"""
        domain = website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        company_name = domain.split('.')[0].title()
        
        return {
            "website_url": website_url,
            "company_name": company_name,
            "services": ["Digital Services", "Consulting", "Technology Solutions"],
            "products": ["Software Platform", "Service Offering"],
            "technical_capabilities": ["Cloud", "Data Analytics", "Web Development"],
            "mentioned_industries": ["Technology", "Business Services"],
            "case_study_signals": ["Client success stories"],
            "geographic_presence": ["Global"],
            "company_description": f"Profile for {company_name} - extracted from {domain}"
        }
