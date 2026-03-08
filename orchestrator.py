"""
MarketLens 2026 - Orchestrator Module (Simplified)
Coordinates 2-agent workflow
Uses LOCAL Ollama LLM (NO PAID APIs)
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

from config import get_ollama_llm
from intelligence_agent import IntelligenceAgentSystem
from strategy_agent import StrategyAgentSystem
from cost_tracker import get_tracker

logger = logging.getLogger(__name__)


class MarketLensOrchestrator:
    """Orchestrates the 2-agent CrewAI workflow"""
    
    def __init__(self, llm: Optional[Any] = None):
        """Initialize orchestrator with LOCAL Ollama LLM"""
        self.llm = llm or get_ollama_llm()
        
        # Initialize agent systems
        self.intelligence_system = IntelligenceAgentSystem(llm=self.llm)
        self.strategy_system = StrategyAgentSystem(llm=self.llm)
        
        logger.info("Orchestrator initialized")
    
    def run_complete_analysis(self, company_url: str, region: str = "Europe") -> Dict[str, Any]:
        """
        Run complete 2-agent analysis workflow with cost tracking
        
        Args:
            company_url: Company website URL to analyze
            region: Target region for analysis
            
        Returns:
            Complete analysis results as dictionary
        """
        # Initialize cost tracker
        tracker = get_tracker()
        tracker.start_tracking()
        
        logger.info("=" * 60)
        logger.info("MARKETLENS 2026 - Starting 2-Agent Analysis")
        logger.info("=" * 60)
        logger.info(f"Company: {company_url}")
        logger.info(f"Region: {region}")
        logger.info("")
        
        try:
            # Step 1: Intelligence Agent
            logger.info("[AGENT 1] INTELLIGENCE - Gathering market signals...")
            tracker.log_agent_start("Intelligence Agent")
            intelligence_results = self._run_intelligence_phase(company_url, region)
            tracker.log_agent_end("Intelligence Agent")
            
            if "error" in intelligence_results:
                logger.error(f"Intelligence phase failed: {intelligence_results['error']}")
                return intelligence_results
            
            logger.info("✅ Intelligence phase complete")
            # Handle both old and new key formats for backward compatibility
            booming_key = 'booming_industries' if 'booming_industries' in intelligence_results else 'booming_industries_europe'
            logger.info(f"   • Found {len(intelligence_results.get(booming_key, []))} booming industries")
            logger.info(f"   • Company: {intelligence_results.get('company_profile', {}).get('company_name', 'Unknown')}")
            logger.info(f"   • Region: {region}")
            logger.info("")
            
            # Step 2: Strategy Agent
            logger.info("[AGENT 2] STRATEGY - Analyzing strategic fit...")
            tracker.log_agent_start("Strategy Agent")
            strategy_results = self._run_strategy_phase(intelligence_results, region)
            tracker.log_agent_end("Strategy Agent")
            
            if "error" in strategy_results:
                logger.error(f"Strategy phase failed: {strategy_results['error']}")
                return strategy_results
            
            logger.info("✅ Strategy phase complete")
            logger.info(f"   • Analyzed {len(strategy_results.get('target_companies', []))} target companies")
            logger.info("")
            
            # Step 3: Combine and validate
            logger.info("[ORCHESTRATOR] Combining and validating results...")
            final_output = self._combine_and_validate(
                intelligence_results,
                strategy_results,
                company_url,
                region
            )
            
            logger.info("✅ Analysis complete and validated")
            
            # Stop tracking and add cost summary to output
            tracker.stop_tracking()
            final_output["cost_and_latency"] = tracker.get_summary()
            
            logger.info("=" * 60)
            
            return final_output
            
        except Exception as e:
            logger.exception("Analysis workflow failed")
            return {
                "error": "Analysis workflow failed",
                "details": str(e),
                "company_url": company_url,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _run_intelligence_phase(self, company_url: str, region: str) -> Dict[str, Any]:
        """Run Intelligence Agent phase"""
        try:
            results = self.intelligence_system.run_intelligence_analysis(
                company_url=company_url,
                region=region
            )
            return results
        except Exception as e:
            logger.error(f"Intelligence phase error: {e}")
            return {"error": str(e)}
    
    def _run_strategy_phase(self, intelligence_data: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Run Strategy Agent phase"""
        try:
            results = self.strategy_system.run_strategy_analysis(
                intelligence_data=intelligence_data,
                region=region
            )
            return results
        except Exception as e:
            logger.error(f"Strategy phase error: {e}")
            return {"error": str(e)}
    
    def _combine_and_validate(
        self,
        intelligence: Dict[str, Any],
        strategy: Dict[str, Any],
        company_url: str,
        region: str
    ) -> Dict[str, Any]:
        """
        Combine results from both agents with generic keys (region-agnostic)
        Handles both old and new key formats for backward compatibility
        """
        # Handle both old (region-specific) and new (generic) key formats
        booming_industries = intelligence.get("booming_industries",
                                             intelligence.get("booming_industries_europe", []))
        trend_signals = intelligence.get("trend_signals",
                                        intelligence.get("europe_trend_signals", {}))

        # Create combined output with generic keys
        combined_output = {
            # Intelligence data (generic keys)
            "company_profile": intelligence.get("company_profile", {}),
            "booming_industries": booming_industries,
            "trend_signals": trend_signals,

            # Strategy data
            "industry_fit_analysis": strategy.get("industry_fit_analysis", {}),
            "strengths_vs_gaps": strategy.get("strengths_vs_gaps", {}),
            "target_audience_profiles": strategy.get("target_audience_profiles", []),
            "opportunity_map_2026": strategy.get("opportunity_map_2026", []),
            "target_companies": strategy.get("target_companies", []),

            # Metadata
            "analysis_metadata": {
                "system": "MarketLens 2026",
                "version": "2.0.0-region-agnostic",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "company_url": company_url,
                "region_analyzed": region,
                "agents_used": [
                    "intelligence_agent",
                    "strategy_agent"
                ],
                "data_sources": f"Live {region} market intelligence"
            }
        }

        logger.info(f"✅ Results combined successfully for {region}")
        return combined_output
    
    def generate_output_filename(self, company_url: str, region: str) -> str:
        """
        Generate output filename with datetime, region, and URL
        Format: outputs/marketlens_<company>_<region>_<datetime>.json
        """
        # Extract company name from URL
        from urllib.parse import urlparse
        parsed = urlparse(company_url)
        domain = parsed.netloc or parsed.path
        # Clean up domain (remove www., extensions, etc.)
        company = domain.replace('www.', '').replace('https://', '').replace('http://', '')
        company = company.split('.')[0]  # Get main domain part
        company = company.replace('/', '_').replace(':', '_')  # Clean special chars
        
        # Generate datetime string
        now = datetime.now()
        datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Create outputs directory if it doesn't exist
        os.makedirs("outputs", exist_ok=True)
        
        # Generate filename
        filename = f"outputs/marketlens_{company}_{region}_{datetime_str}.json"
        return filename
    
    def save_results(self, results: Dict[str, Any], filepath: str = None, company_url: str = None, region: str = None) -> str:
        """
        Save results to JSON file
        If filepath is None, generates filename from company_url and region
        """
        # Generate filename if not provided
        if filepath is None and company_url and region:
            filepath = self.generate_output_filename(company_url, region)
        elif filepath is None:
            filepath = "marketlens_output.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise


# Convenience function for direct usage
def analyze_company(company_url: str, region: str = "Europe") -> Dict[str, Any]:
    """
    Convenience function to analyze a company
    
    Args:
        company_url: Company website URL
        region: Target region (default: Europe)
        
    Returns:
        Analysis results dictionary
    """
    orchestrator = MarketLensOrchestrator()
    return orchestrator.run_complete_analysis(company_url, region)


if __name__ == "__main__":
    # Test the orchestrator with region support
    import sys
    logging.basicConfig(level=logging.INFO)

    # Get region from command line or default to Europe
    test_region = sys.argv[1] if len(sys.argv) > 1 else "Europe"
    test_url = sys.argv[2] if len(sys.argv) > 2 else "https://xerago.com"

    print(f"Testing orchestrator for {test_region}...")
    print("=" * 60)

    result = analyze_company(test_url, test_region)

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Success! Analyzed: {result['company_profile'].get('company_name')}")
        print(f"Region: {result.get('analysis_metadata', {}).get('region_analyzed', 'Unknown')}")
        print(f"Industries: {len(result.get('booming_industries', []))}")
        print(f"Targets: {len(result.get('target_companies', []))}")

        print("\nTest with different regions:")
        print("  python orchestrator.py Europe")
        print("  python orchestrator.py Asia")
        print("  python orchestrator.py 'United States'")
        print("  python orchestrator.py China")
