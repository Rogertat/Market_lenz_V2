"""
Agent 1: Intelligence Agent (Simplified)
Role: Pure intelligence gathering + structured synthesis
Uses CrewAI framework with LOCAL Ollama LLM (NO PAID APIs)
Uses LIVE market data (NO HARDCODED DATA)
Region-agnostic design supports global market intelligence
"""
import logging
from typing import Dict, List, Any
from crewai import Agent, Task, Crew, Process

from config import Config, get_ollama_llm
from web_scraper import WebScraperTool
from live_market_data import LiveMarketDataCollector

logger = logging.getLogger(__name__)


class IntelligenceAgentSystem:
    """
    Agent 1: Intelligence Agent (Simplified)
    Gathers company intelligence and market signals for any region
    Region-agnostic design supports global market intelligence
    """

    def __init__(self, llm=None):
        self.config = Config()
        self.llm = llm or get_ollama_llm(temperature=0.2)
        self.web_scraper = WebScraperTool()
        # market_data_collector is now created per-region in run_intelligence_analysis()
        
    def create_intelligence_agent(self) -> Agent:
        """Create the Intelligence Agent"""
        return Agent(
            role="Intelligence Analyst",
            goal="Gather company intelligence and identify the market opportunities",
            backstory="""You are an expert market intelligence analyst.
            You extract company information from websites and identify booming industries.
            You provide structured, evidence-based intelligence in JSON format.
            You are thorough, accurate, and data-driven in your analysis.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def run_intelligence_analysis(self, company_url: str, region: str = "Europe") -> Dict[str, Any]:
        """
        Run complete intelligence analysis using CrewAI.
        Simplified: ONE task that gathers all intelligence.
        Works for any region - dynamically loads region-specific data sources.

        Args:
            company_url: Company website URL to analyze
            region: Target region (e.g., "Europe", "Asia", "United States", "China")

        Returns:
            Dictionary with company profile, booming industries, and trend signals
        """
        logger.info("=" * 60)
        logger.info(f"AGENT 1: INTELLIGENCE - Starting Analysis for {region}")
        logger.info("=" * 60)

        # Get company data from web scraper first
        company_data = self.web_scraper.extract_company_profile(company_url)
        logger.info(f"✅ Extracted company: {company_data.get('company_name', 'Unknown')}")

        # Create region-specific market data collector
        market_data_collector = LiveMarketDataCollector(region=region)

        # Get market signals for the specified region - LIVE DATA (NO HARDCODING)
        logger.info(f"🌐 Gathering LIVE {region} market signals from internet...")
        market_signals = market_data_collector.get_live_market_signals(limit=30)
        logger.info(f"✅ Collected {len(market_signals)} LIVE {region} market signals (NO HARDCODED DATA)")
        
        # Create ONE comprehensive task
        intelligence_agent = self.create_intelligence_agent()
        
        task = Task(
            description=f"""
            Analyze the company and {region} market to produce strategic intelligence.

            COMPANY INFORMATION:
            {self._format_company_data(company_data)}

            MARKET SIGNALS FROM {region.upper()} (2026):
            {self._format_market_signals(market_signals)}

            YOUR TASK:
            Produce a comprehensive intelligence report in JSON format with these sections:

            1. company_profile: {{
                "website_url": "{company_url}",
                "company_name": "name",
                "services": ["service1", "service2"],
                "products": ["product1", "product2"],
                "technical_capabilities": ["capability1", "capability2"],
                "mentioned_industries": ["industry1", "industry2"],
                "geographic_presence": ["region1", "region2"],
                "company_description": "brief description"
            }}

            2. booming_industries: [
                {{
                    "industry": "Industry Name",
                    "growth_signals": ["signal1", "signal2", "signal3"],
                    "market_size": "$XXB by 2026",
                    "key_drivers": ["driver1", "driver2"],
                    "why_booming": "Evidence-based explanation from {region} market"
                }}
            ] (Provide 5-7 booming industries in {region} based on the market signals)

            3. trend_signals: {{
                "industry_growth_indicators": [
                    {{"industry": "name", "growth_rate": "XX%", "driver": "description", "source": "source"}}
                ],
                "technology_trends": [
                    {{"technology": "name", "adoption_rate": "XX%", "trend": "increasing/stable", "key_markets": ["market1"]}}
                ],
                "regulatory_changes": [
                    {{"regulation": "name", "impact": "description", "opportunity": "opportunity"}}
                ]
            }}

            REQUIREMENTS:
            - Base findings on actual company data and {region} market signals provided
            - Be specific and evidence-based
            - Return ONLY valid JSON, no markdown, no code blocks, no explanation
            - Ensure all arrays have at least 3-5 items
            - Focus on {region} market opportunities and trends
            """,
            expected_output=f"Complete intelligence report for {region} in valid JSON format",
            agent=intelligence_agent
        )
        
        # Create crew and execute
        crew = Crew(
            agents=[intelligence_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        logger.info("✅ Intelligence analysis completed")
        
        # Parse the JSON result
        parsed_result = self._parse_json_result(result)
        
        # Ensure we have company data even if parsing fails
        if "error" in parsed_result or "company_profile" not in parsed_result:
            logger.warning(f"Using fallback with LIVE {region} market data")
            # Use LIVE data for fallback - NO HARDCODING
            live_intelligence = self._get_live_fallback_data(company_data, market_signals, market_data_collector, region)
            return live_intelligence

        return parsed_result
    
    def _format_company_data(self, company_data: Dict) -> str:
        """Format company data for prompt"""
        return f"""
        Company: {company_data.get('company_name', 'Unknown')}
        Services: {', '.join(company_data.get('services', [])[:10])}
        Products: {', '.join(company_data.get('products', [])[:10])}
        Capabilities: {', '.join(company_data.get('technical_capabilities', [])[:10])}
        Industries: {', '.join(company_data.get('mentioned_industries', [])[:10])}
        Description: {company_data.get('company_description', '')[:300]}
        """
    
    def _format_market_signals(self, signals: List[Dict]) -> str:
        """Format market signals for prompt"""
        formatted = []
        for i, signal in enumerate(signals[:30], 1):  # Top 30 signals
            formatted.append(f"{i}. {signal.get('industry', 'General')}: {signal.get('title', '')}")
        return '\n'.join(formatted)
    
    def _get_live_fallback_data(self, company_data: Dict, market_signals: List[Dict],
                                market_data_collector, region: str) -> Dict:
        """
        Generate fallback data using LIVE market intelligence
        NO HARDCODED DATA - Uses real market signals collected from internet

        Args:
            company_data: Company profile data
            market_signals: List of market signal dictionaries
            market_data_collector: LiveMarketDataCollector instance
            region: Target region

        Returns:
            Dictionary with company profile, booming industries, and trend signals
        """
        logger.info(f"📊 Analyzing LIVE {region} market signals for fallback data...")

        # Analyze booming industries from LIVE signals
        booming_industries = market_data_collector.analyze_booming_industries(market_signals)
        logger.info(f"   ✓ Identified {len(booming_industries)} booming industries from LIVE {region} data")

        # Extract trends from LIVE signals
        trends = market_data_collector.get_industry_trends(market_signals)
        logger.info(f"   ✓ Extracted industry trends from LIVE {region} signals")

        return {
            "company_profile": company_data,
            "booming_industries": booming_industries,  # Generic key (not region-specific)
            "trend_signals": trends,  # Generic key (not region-specific)
            "region": region,
            "data_source": f"LIVE {region} market intelligence - NO HARDCODED DATA"
        }
    
    def _parse_json_result(self, result) -> Dict[str, Any]:
        """Parse JSON result with multiple fallback strategies"""
        import json
        import re
        
        # Handle different result types from CrewAI
        if isinstance(result, dict):
            return result
        
        if not isinstance(result, str):
            result = str(result)
        
        result = result.strip()
        
        # Try 1: Direct JSON parse
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
        
        # Try 2: Extract JSON from markdown code blocks
        json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        matches = re.findall(json_block_pattern, result)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        
        # Try 3: Find JSON object between curly braces
        json_object_pattern = r'\{[\s\S]*\}'
        match = re.search(json_object_pattern, result)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Failed to parse intelligence result as JSON")
        return {"error": "JSON parsing failed"}
