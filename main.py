"""
MarketLens 2026 - Main Entry Point
2-Agent Strategic Intelligence System
"""
import argparse
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print system banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              MARKETLENS 2026                                 ║
║         AI-Powered Strategic Opportunity Analyzer            ║
║                                                              ║
║      2-Agent System | LOCAL Ollama LLM | LIVE Data           ║
║      NO PAID APIs | NO HARDCODED DATA                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MarketLens 2026 - Strategic Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --url https://xerago.com
  python main.py --url https://example.com --region Europe
  python main.py --verbose
        """
    )
    
    parser.add_argument(
        "--url",
        default="https://xerago.com",
        help="Company website URL to analyze (default: https://xerago.com)"
    )
    parser.add_argument(
        "--region",
        default="Europe",
        help="Target region for analysis (default: Europe)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (default: auto-generated)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print banner
    print_banner()
    
    # Check for Ollama (no API key needed!)
    import os
    print("🔧 Using LOCAL Ollama LLM (NO PAID API)")
    print("   Make sure Ollama is installed and running:")
    print("   1. Install: https://ollama.ai/download")
    print("   2. Start: ollama serve")
    print(f"   3. Pull model: ollama pull {os.getenv('OLLAMA_MODEL', 'llama3.2')}")
    print()
    
    # Import orchestrator
    try:
        from orchestrator import MarketLensOrchestrator
    except ImportError as e:
        print(f"\n❌ Error: Failed to import orchestrator: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Print configuration
    print(f"⚙️  Configuration:")
    print(f"   • LLM: LOCAL Ollama (FREE, NO PAID API)")
    print(f"   • Model: {os.getenv('OLLAMA_MODEL', 'llama3.2')}")
    print(f"   • Temperature: {os.getenv('OLLAMA_TEMPERATURE', '0.2')}")
    print(f"   • Data Source: LIVE from internet (NO HARDCODED DATA)")
    print(f"   • Company: {args.url}")
    print(f"   • Region: {args.region}")
    print()
    
    # Run analysis
    try:
        from cost_tracker import get_tracker, reset_tracker
        
        # Reset tracker for new run
        reset_tracker()
        
        orchestrator = MarketLensOrchestrator()
        results = orchestrator.run_complete_analysis(
            company_url=args.url,
            region=args.region
        )
        
        # Save results with smart filename generation
        if args.output:
            output_file = args.output
        else:
            # Generate filename from URL and region
            output_file = None  # Will be auto-generated
        
        output_file = orchestrator.save_results(
            results, 
            filepath=output_file,
            company_url=args.url,
            region=args.region
        )
        
        # Get cost tracker and print summary
        tracker = get_tracker()
        tracker.print_summary()
        
        # Save cost report
        cost_report_file = output_file.replace('.json', '_cost_report.json')
        tracker.save_report(cost_report_file)
        
        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        
        if "error" in results:
            print(f"❌ Analysis failed: {results['error']}")
            if "details" in results:
                print(f"Details: {results['details']}")
            sys.exit(1)
        
        company_name = results.get("company_profile", {}).get("company_name", "Unknown")
        # Handle both old and new key formats
        industries = len(results.get("booming_industries", results.get("booming_industries_europe", [])))
        targets = len(results.get("target_companies", []))
        region_analyzed = results.get("analysis_metadata", {}).get("region_analyzed", args.region)

        print(f"✅ Company: {company_name}")
        print(f"✅ Region: {region_analyzed}")
        print(f"✅ Industries analyzed: {industries}")
        print(f"✅ Target companies: {targets}")
        print(f"✅ Output saved: {output_file}")
        print(f"✅ Cost report: {cost_report_file}")
        print("=" * 60)
        
    except Exception as e:
        logger.exception("Analysis failed")
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
