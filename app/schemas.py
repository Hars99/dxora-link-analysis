from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class AnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LinkAnalysisRequest(BaseModel):
    url: HttpUrl


class Brand(AnalysisModel):
    name: str
    category: str
    summary: str
    products_and_services: list[str]


class Competitor(AnalysisModel):
    name: str
    overlap: str
    strengths: list[str]
    possible_gaps: list[str]


class CompetitorAnalysis(AnalysisModel):
    brand_strengths: list[str]
    opportunities: list[str]
    ai_suggested_competitors: list[Competitor] = Field(max_length=5)


Platform = Literal["Google", "Facebook", "Instagram", "LinkedIn", "X"]


class SearchQuery(AnalysisModel):
    query: str
    platforms: list[Platform] = Field(min_length=1)
    intent: str
    business_relevance: str
    target_audience: str


class SEOImprovements(AnalysisModel):
    primary_keyword: str
    secondary_keywords: list[str]
    long_tail_keywords: list[str]
    recommended_title: str
    meta_description: str
    supporting_content: list[str]


class Service(AnalysisModel):
    name: str
    description: str
    target_industry: str
    target_customer: str
    main_benefit: str
    evidence_type: Literal["website_content", "inferred"]


class TargetAudience(AnalysisModel):
    primary_audience: list[str]
    secondary_audience: list[str]
    industries: list[str]
    business_types: list[str]
    customer_profiles: list[str]
    geography: str | None
    customer_needs: list[str]
    interests: list[str]
    recommended_segments: list[str]


class Analysis(AnalysisModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: list[SearchQuery] = Field(min_length=5, max_length=5)
    seo_improvements: SEOImprovements
    top_services: list[Service] = Field(max_length=5)
    target_audience: TargetAudience

    @field_validator("target_search_queries")
    @classmethod
    def check_platform_coverage(cls, queries: list[SearchQuery]) -> list[SearchQuery]:
        if len({query.query.strip().casefold() for query in queries}) != 5:
            raise ValueError("Include five distinct search queries.")

        platforms = {platform for query in queries for platform in query.platforms}
        if platforms != {"Google", "Facebook", "Instagram", "LinkedIn", "X"}:
            raise ValueError("Include all five search platforms.")

        return queries


class AnalysisData(AnalysisModel):
    brand: Brand
    analysis: Analysis


class LinkAnalysisResponse(AnalysisData):
    success: bool
    website: str