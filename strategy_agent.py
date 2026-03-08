"""
Agent 2: Strategy Agent (Simplified)
Role: Strategic fit analysis + opportunity mapping
Uses CrewAI framework with LOCAL Ollama LLM (NO PAID APIs)
Uses DYNAMIC target companies (NO HARDCODED COMPANIES)
Region-agnostic design supports global market strategy
"""
import logging
from typing import Dict, List, Any
from crewai import Agent, Task, Crew, Process

from config import Config, get_ollama_llm
from target_company_finder import TargetCompanyFinder

logger = logging.getLogger(__name__)


class StrategyAgentSystem:
    """
    Agent 2: Strategy Agent (Simplified)
    Analyzes strategic fit and identifies opportunities for any region
    Region-agnostic design supports global market strategy
    """

    def __init__(self, llm=None):
        self.config = Config()
        self.llm = llm or get_ollama_llm(temperature=0.3)
        # company_finder is now created per-region in run_strategy_analysis()
        
    def create_strategy_agent(self) -> Agent:
        """Create the Strategy Agent"""
        return Agent(
            role="Strategic Consultant",
            goal="Analyze strategic fit, identify opportunities, and recommend target companies",
            backstory="""You are an expert strategy consultant specializing in market entry and business development.
            You analyze company capabilities against market opportunities to provide actionable strategic recommendations.
            You are analytical, data-driven, and focused on practical business outcomes.
            You provide structured strategic insights in JSON format.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def run_strategy_analysis(self, intelligence_data: Dict[str, Any], region: str = "Europe") -> Dict[str, Any]:
        """
        Run complete strategy analysis using CrewAI.
        Simplified: ONE task that does all strategic analysis.
        Works for any region - adapts analysis to regional market dynamics.

        Args:
            intelligence_data: Output from intelligence agent
            region: Target region (e.g., "Europe", "Asia", "United States", "China")

        Returns:
            Dictionary with strategic analysis and target companies
        """
        logger.info("=" * 60)
        logger.info(f"AGENT 2: STRATEGY - Starting Analysis for {region}")
        logger.info("=" * 60)

        company_profile = intelligence_data.get("company_profile", {})

        # Handle both old and new key formats for backward compatibility
        booming_industries = intelligence_data.get("booming_industries",
                                                   intelligence_data.get("booming_industries_europe", []))
        
        # Create ONE comprehensive strategy task
        strategy_agent = self.create_strategy_agent()
        
        task = Task(
            description=f"""
            Perform comprehensive strategic analysis for {region} market entry.

            COMPANY PROFILE:
            - Name: {company_profile.get('company_name', 'Unknown')}
            - Services: {', '.join(company_profile.get('services', [])[:10])}
            - Products: {', '.join(company_profile.get('products', [])[:10])}
            - Capabilities: {', '.join(company_profile.get('technical_capabilities', [])[:10])}
            - Industries: {', '.join(company_profile.get('mentioned_industries', [])[:10])}

            BOOMING {region.upper()} INDUSTRIES:
            {self._format_industries(booming_industries)}

            YOUR TASK:
            Produce a comprehensive strategic analysis for {region} in JSON format with these sections:

            1. industry_fit_analysis: {{
                "strong_fit_industries": [
                    {{
                        "industry": "Industry Name",
                        "fit_score": 0.85,
                        "reasoning": "Why company fits well in {region}",
                        "market_size": "$XXB",
                        "growth_signals": ["signal1", "signal2"]
                    }}
                ] (3-5 industries in {region} where company has strong existing fit),
                "no_footprint_but_high_potential": [
                    {{
                        "industry": "Industry Name",
                        "fit_score": 0.75,
                        "why_booming": ["reason1", "reason2"],
                        "entry_opportunity": "Strategic approach for {region}",
                        "risk_considerations": ["risk1", "risk2"],
                        "market_size": "$XXB"
                    }}
                ] (2-3 {region} industries with no current footprint but high potential)
            }}

            2. strengths_vs_gaps: {{
                "competitive_strengths": [
                    {{
                        "strength": "Specific capability",
                        "market_demand": "Why this matters in {region}",
                        "evidence": "Data point or trend from {region}"
                    }}
                ] (4-6 key strengths for {region} market),
                "capability_gaps": [
                    {{
                        "gap": "Missing capability",
                        "market_opportunity": "What this blocks in {region}",
                        "recommendation": "How to address for {region} market"
                    }}
                ] (3-4 key gaps for {region} market)
            }}
            
            3. target_audience_profiles: [
                {{
                    "ideal_customer_type": "E.g., Digital Banks in {region}",
                    "industry_vertical": "Industry name",
                    "company_maturity": "startup/scale-up/enterprise",
                    "decision_maker_persona": "CTO, VP Engineering, etc.",
                    "pain_points": ["pain1", "pain2", "pain3"],
                    "value_proposition": "How company solves their problems in {region} market"
                }}
            ] (3-4 distinct target profiles in {region})

            4. opportunity_map_2026: [
                {{
                    "opportunity_theme": "E.g., AI Compliance Solutions in {region}",
                    "why_2026_strategic": "Timing and market readiness in {region}",
                    "supporting_signals": ["signal1 from {region}", "signal2", "signal3"],
                    "expected_business_impact": "$XXM revenue potential in {region}",
                    "required_capabilities": ["capability1", "capability2"]
                }}
            ] (4-6 opportunity themes specific to {region} market)

            5. target_companies: [
                {{
                    "company": "Real company name from {region}",
                    "industry": "Industry from booming list",
                    "strategic_relevance": "Why target them in {region}",
                    "data_backed_reasoning": "Evidence-based rationale"
                }}
            ] (8-12 real {region} companies as strategic targets)

            REQUIREMENTS:
            - Base all analysis on provided intelligence data from {region}
            - Be specific and actionable for {region} market
            - Use real company names from {region} for targets
            - Return ONLY valid JSON, no markdown, no code blocks, no explanation
            - Ensure all arrays have minimum items as specified
            - Focus on {region}-specific market dynamics and opportunities
            """,
            expected_output=f"Complete strategic analysis for {region} in valid JSON format",
            agent=strategy_agent
        )
        
        # Create crew and execute
        crew = Crew(
            agents=[strategy_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        logger.info("✅ Strategy analysis completed")
        
        # Parse the JSON result
        parsed_result = self._parse_json_result(result)
        
        # Provide fallback if parsing fails
        if "error" in parsed_result:
            logger.warning(f"Using fallback strategy with DYNAMIC {region} data")
            return self._get_dynamic_fallback_strategy(company_profile, booming_industries, region)

        return parsed_result
    
    def _format_industries(self, industries: List[Dict]) -> str:
        """Format booming industries for prompt"""
        formatted = []
        for i, ind in enumerate(industries[:10], 1):
            formatted.append(f"{i}. {ind.get('industry', 'Unknown')}: {ind.get('why_booming', '')[:100]}")
        return '\n'.join(formatted)
    
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
        
        logger.error(f"Failed to parse strategy result as JSON")
        return {"error": "JSON parsing failed"}
    
    def _get_dynamic_fallback_strategy(self, company_profile: Dict, industries: List[Dict], region: str) -> Dict:
        """
        Generate fallback strategy using DYNAMIC data
        NO HARDCODED COMPANIES - Finds real companies from internet

        Args:
            company_profile: Company profile dictionary
            industries: List of booming industries
            region: Target region

        Returns:
            Dictionary with strategic analysis
        """
        company_name = company_profile.get("company_name", "Company")
        logger.info(f"🔍 Generating strategy with DYNAMIC {region} target companies (NO HARDCODED DATA)...")

        # Create region-specific company finder
        company_finder = TargetCompanyFinder(region=region)

        # Find REAL target companies dynamically
        logger.info(f"   Discovering real {region} companies from web sources...")
        industry_names = [ind.get('industry', '') for ind in industries[:8]]
        target_companies = company_finder.find_target_companies(industry_names, limit=12)

        # Enrich with market data
        enriched_companies = company_finder.enrich_company_data(target_companies, industries)
        logger.info(f"   ✓ Found {len(enriched_companies)} real {region} companies dynamically")

        # Build strategy based on actual industry data
        strong_fit = []
        new_opportunities = []

        for i, industry in enumerate(industries[:5]):
            if i < 3:
                # Strong fit industries
                strong_fit.append({
                    "industry": industry.get("industry", "Technology"),
                    "fit_score": 0.80 + (i * 0.05),
                    "reasoning": f"{company_name}'s capabilities align with {industry.get('industry', 'this sector')}",
                    "market_size": f"{industry.get('signal_count', 'Multiple')} market signals detected",
                    "growth_signals": industry.get("growth_signals", ["Market growth detected"])[:3]
                })
            else:
                # New opportunity industries
                new_opportunities.append({
                    "industry": industry.get("industry", "Technology"),
                    "fit_score": 0.70,
                    "why_booming": industry.get("growth_signals", ["Growing market"])[:3],
                    "entry_opportunity": f"Enter {industry.get('industry', 'market')} with technical capabilities",
                    "risk_considerations": ["Market competition", "Domain expertise needed"],
                    "market_size": f"{industry.get('signal_count', 'Multiple')} signals"
                })

        return {
            "industry_fit_analysis": {
                "strong_fit_industries": strong_fit,
                "no_footprint_but_high_potential": new_opportunities
            },
            "strengths_vs_gaps": {
                "competitive_strengths": [
                    {
                        "strength": f"{company_name}'s technical capabilities",
                        "market_demand": f"Strong demand for digital transformation in {region}",
                        "evidence": f"Based on analysis of {len(industries)} booming {region} industries"
                    }
                ],
                "capability_gaps": [
                    {
                        "gap": f"{region} market expertise",
                        "market_opportunity": f"Build local partnerships for {region} market entry",
                        "recommendation": f"Partner with {region} companies or hire local experts"
                    }
                ]
            },
            "target_audience_profiles": [
                {
                    "ideal_customer_type": f"{industries[0].get('industry', 'Technology')} Companies",
                    "industry_vertical": industries[0].get('industry', 'Technology'),
                    "company_maturity": "scale-up to enterprise",
                    "decision_maker_persona": "CTO, VP Engineering, Head of Digital",
                    "pain_points": ["Digital transformation", "Market competitiveness", "Technology adoption"],
                    "value_proposition": f"{company_name} provides technical expertise for market growth"
                }
            ],
            "opportunity_map_2026": [
                {
                    "opportunity_theme": f"{industries[0].get('industry', 'Technology')} Solutions in {region}",
                    "why_2026_strategic": f"Strong market signals in {region} {industries[0].get('industry', 'sector')}",
                    "supporting_signals": industries[0].get("growth_signals", ["Market growth"])[:3],
                    "expected_business_impact": f"Significant revenue potential in growing {region} market",
                    "required_capabilities": company_profile.get("technical_capabilities", ["Technical expertise"])[:3]
                }
            ],
            "target_companies": enriched_companies,  # REAL companies found dynamically
            "region": region,
            "data_source": f"DYNAMIC {region} discovery - NO HARDCODED COMPANIES"
        }
