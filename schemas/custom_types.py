from pydantic import BaseModel, HttpUrl

class AuditRequest(BaseModel):
    url: HttpUrl                    # validates it's a real URL before anything runs


class MetaMetrics(BaseModel):
    title: str
    description: str

class HeadingMetrics(BaseModel):
    h1_count: int
    h2_count: int
    h3_count: int
    h1: list[str]
    h2: list[str]
    h3: list[str]

class ImageMetrics(BaseModel):
    total: int
    missing_alt: int
    pct_missing_alt: float

class LinkMetrics(BaseModel):
    internal_count: int
    external_count: int

class CTAMetrics(BaseModel):
    total: int

class ContentMetrics(BaseModel):
    word_count: int

class Insight(BaseModel):
    seo_structure: str
    messaging_clarity: str
    cta_usage: str
    content_depth: str
    ux_structure: str

class Recommendation(BaseModel):
    priority: int
    title: str
    reasoning: str

class AuditResponse(BaseModel):
    url: str
    meta: MetaMetrics
    headings: HeadingMetrics
    images: ImageMetrics
    links: LinkMetrics
    ctas: CTAMetrics
    content: ContentMetrics
    insights: Insight
    recommendations: list[Recommendation]