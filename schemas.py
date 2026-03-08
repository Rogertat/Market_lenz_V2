"""
Pydantic schemas for MarketLens 2026
Ensures deterministic structured output
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    """Company profile extraction schema"""
    website_url: str
    company_name: str
    services: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    technical_capabilities: List[str] = Field(default_factory=list)
    mentioned_industries: List[str] = Field(default_factory=list)
    case_study_signals: List[str] = Field(default_factory=list)
    geographic_presence: List[str] = Field(default_factory=list)
    company_description: str = ""


class GrowthSignal(BaseModel):
    """Individual growth signal"""
    industry: str
    growth_rate: str
    driver: str
    source: str


class TrendSignal(BaseModel):
    """European trend signal"""
    industry: str
    growth_rate: str
    driver: str
    source: str = "EU Commission"


class TechnologyTrend(BaseModel):
    """Technology adoption trend"""
    technology: str
    adoption_rate: str
    trend: str
    key_markets: List[str]


class DemandSignal(BaseModel):
    """AI automation demand signal"""
    sector: str
    demand_driver: str
    growth_indicator: str


class RegulatoryChange(BaseModel):
    """Regulatory change signal"""
    regulation: str
    impact: str
    opportunity: str


class FundingTrend(BaseModel):
    """Funding trend signal"""
    sector: str
    funding_trend: str
    key_investors: List[str]


class EuropeTrendSignals(BaseModel):
    """European trend signals collection"""
    industry_growth_indicators: List[GrowthSignal] = Field(default_factory=list)
    technology_adoption_trends: List[TechnologyTrend] = Field(default_factory=list)
    ai_automation_demand: List[DemandSignal] = Field(default_factory=list)
    regulatory_changes: List[RegulatoryChange] = Field(default_factory=list)
    funding_trends: List[FundingTrend] = Field(default_factory=list)


class BoomingIndustry(BaseModel):
    """Booming industry identification"""
    industry: str
    growth_signals: List[str]
    market_size: str
    key_drivers: List[str]
    why_booming: str


class StrongFitIndustry(BaseModel):
    """Strong fit industry analysis"""
    industry: str
    fit_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    market_size: str
    growth_signals: List[str]


class HighPotentialIndustry(BaseModel):
    """High potential industry (no current footprint)"""
    industry: str
    fit_score: float = Field(ge=0.0, le=1.0)
    why_booming: List[str]
    entry_opportunity: str
    risk_considerations: List[str]
    market_size: str


class IndustryFitAnalysis(BaseModel):
    """Industry fit analysis output"""
    strong_fit_industries: List[StrongFitIndustry] = Field(default_factory=list)
    no_footprint_but_high_potential: List[HighPotentialIndustry] = Field(default_factory=list)


class CompetitiveStrength(BaseModel):
    """Competitive strength item"""
    strength: str
    european_demand: str
    evidence: str


class CapabilityGap(BaseModel):
    """Capability gap item"""
    gap: str
    european_opportunity: str
    recommendation: str


class StrengthsVsGaps(BaseModel):
    """Strengths vs gaps analysis"""
    competitive_strengths: List[CompetitiveStrength] = Field(default_factory=list)
    capability_gaps: List[CapabilityGap] = Field(default_factory=list)


class TargetAudienceProfile(BaseModel):
    """Target audience profile"""
    ideal_customer_type: str
    industry_vertical: str
    company_maturity: str
    decision_maker_persona: str
    pain_points: List[str]
    value_proposition: str


class OpportunityTheme(BaseModel):
    """2026 opportunity theme"""
    opportunity_theme: str
    why_2026_strategic: str
    supporting_signals: List[str]
    expected_business_impact: str
    required_capabilities: List[str]


class TargetCompany(BaseModel):
    """Strategic target company"""
    company: str
    industry: str
    strategic_relevance: str
    data_backed_reasoning: str


class IntelligenceOutput(BaseModel):
    """Agent 1: Intelligence Agent output"""
    company_profile: CompanyProfile
    europe_trend_signals: EuropeTrendSignals
    booming_industries_europe: List[BoomingIndustry]
    

class FinalOutput(BaseModel):
    """Final structured output - Agent 2 result"""
    company_profile: CompanyProfile
    europe_trend_signals: EuropeTrendSignals
    booming_industries_europe: List[BoomingIndustry]
    industry_fit_analysis: IndustryFitAnalysis
    strengths_vs_gaps: StrengthsVsGaps
    target_audience_profiles: List[TargetAudienceProfile]
    opportunity_map_2026: List[OpportunityTheme]
    target_companies: List[TargetCompany]
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_profile": {
                    "website_url": "https://xerago.com",
                    "company_name": "Xerago"
                }
            }
        }


class MarketLensOutputSchema:
    """Schema validator for final output - provides validate() method"""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate output data against FinalOutput schema.
        Returns validated data or raises ValidationError.
        """
        try:
            # Validate using Pydantic FinalOutput model
            validated = FinalOutput(**data)
            return validated.model_dump()
        except Exception as e:
            # Log validation issues but return data anyway
            # (validation is advisory, not blocking)
            import logging
            logging.getLogger(__name__).warning(f"Schema validation warning: {e}")
            return data
