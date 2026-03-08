"""
Cost and Latency Tracking for MarketLens 2026
Tracks API usage, tokens, latency, and calculates costs based on Groq pricing
"""
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Tracks costs and latency for Groq API calls
    
    Groq Pricing (as of 2026):
    - llama3-70b-8192: $0.59/M input tokens, $0.79/M output tokens
    - llama3-8b-8192: $0.05/M input tokens, $0.08/M output tokens
    - mixtral-8x7b-32768: $0.24/M input tokens, $0.24/M output tokens
    - qwen/qwen3-32b: $0.20/M input tokens, $0.20/M output tokens (estimated)
    - gemma-7b-it: $0.07/M input tokens, $0.07/M output tokens
    """
    
    # Pricing per million tokens (USD)
    PRICING = {
        "llama3-70b-8192": {"input": 0.59, "output": 0.79},
        "llama3-8b-8192": {"input": 0.05, "output": 0.08},
        "llama3.2": {"input": 0.0, "output": 0.0},  # Ollama local - FREE
        "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
        "qwen/qwen3-32b": {"input": 0.20, "output": 0.20},
        "gemma-7b-it": {"input": 0.07, "output": 0.07},
        "default": {"input": 0.0, "output": 0.0}  # Local Ollama - FREE
    }
    
    def __init__(self, model: str = None):
        # Import here to avoid circular dependency
        if model is None:
            from config import Config
            model = Config.OLLAMA_MODEL
        self.model = model
        self.start_time = None
        self.end_time = None
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.api_calls = 0
        self.agent_timings = {}
        
    def start_tracking(self):
        """Start tracking execution time"""
        self.start_time = time.time()
        logger.info("⏱️  Cost tracking started")
    
    def stop_tracking(self):
        """Stop tracking execution time"""
        self.end_time = time.time()
        logger.info("⏱️  Cost tracking stopped")
    
    def log_agent_start(self, agent_name: str):
        """Log start time for an agent"""
        self.agent_timings[agent_name] = {"start": time.time()}
    
    def log_agent_end(self, agent_name: str):
        """Log end time for an agent"""
        if agent_name in self.agent_timings:
            self.agent_timings[agent_name]["end"] = time.time()
            self.agent_timings[agent_name]["duration"] = (
                self.agent_timings[agent_name]["end"] - 
                self.agent_timings[agent_name]["start"]
            )
    
    def add_api_call(self, input_tokens: int, output_tokens: int):
        """Record an API call with token usage"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.api_calls += 1
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def get_total_latency(self) -> float:
        """Get total execution time in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def calculate_cost(self) -> Dict[str, float]:
        """Calculate total cost based on token usage"""
        pricing = self.PRICING.get(self.model, self.PRICING["default"])
        
        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete tracking summary"""
        costs = self.calculate_cost()
        total_latency = self.get_total_latency()
        
        # Calculate agent latencies
        agent_latencies = {}
        for agent_name, timing in self.agent_timings.items():
            if "duration" in timing:
                agent_latencies[agent_name] = round(timing["duration"], 2)
        
        summary = {
            "tracking_info": {
                "model": self.model,
                "total_latency_seconds": round(total_latency, 2),
                "total_latency_minutes": round(total_latency / 60, 2),
                "agent_latencies_seconds": agent_latencies
            },
            "token_usage": {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "api_calls_count": self.api_calls
            },
            "cost_breakdown": {
                "model": self.model,
                "input_tokens_cost_usd": costs["input_cost_usd"],
                "output_tokens_cost_usd": costs["output_cost_usd"],
                "total_cost_usd": costs["total_cost_usd"],
                "pricing_per_1m_tokens": self.PRICING.get(self.model, self.PRICING["default"])
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return summary
    
    def print_summary(self):
        """Print formatted cost and latency summary"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("💰 COST & LATENCY REPORT")
        print("=" * 60)
        print(f"⏱️  Total Execution Time: {summary['tracking_info']['total_latency_seconds']}s " +
              f"({summary['tracking_info']['total_latency_minutes']} min)")
        
        if summary['tracking_info']['agent_latencies_seconds']:
            print("\n📊 Agent Latencies:")
            for agent, latency in summary['tracking_info']['agent_latencies_seconds'].items():
                print(f"   • {agent}: {latency}s")
        
        print(f"\n🔢 Token Usage:")
        print(f"   • Input Tokens: {summary['token_usage']['total_input_tokens']:,}")
        print(f"   • Output Tokens: {summary['token_usage']['total_output_tokens']:,}")
        print(f"   • Total Tokens: {summary['token_usage']['total_tokens']:,}")
        print(f"   • API Calls: {summary['token_usage']['api_calls_count']}")
        
        print(f"\n💵 Cost Breakdown (Model: {summary['cost_breakdown']['model']}):")
        print(f"   • Input Cost: ${summary['cost_breakdown']['input_tokens_cost_usd']:.6f}")
        print(f"   • Output Cost: ${summary['cost_breakdown']['output_tokens_cost_usd']:.6f}")
        print(f"   • Total Cost: ${summary['cost_breakdown']['total_cost_usd']:.6f}")
        print(f"   • Pricing: ${summary['cost_breakdown']['pricing_per_1m_tokens']['input']}/M input, " +
              f"${summary['cost_breakdown']['pricing_per_1m_tokens']['output']}/M output")
        
        print("=" * 60 + "\n")
    
    def save_report(self, filepath: str):
        """Save tracking report to JSON file"""
        summary = self.get_summary()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"Cost report saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save cost report: {e}")


# Singleton instance for global tracking
_tracker_instance: Optional[CostTracker] = None


def get_tracker(model: str = None) -> CostTracker:
    """Get or create global cost tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = CostTracker(model)
    return _tracker_instance


def reset_tracker():
    """Reset global tracker instance"""
    global _tracker_instance
    _tracker_instance = None
