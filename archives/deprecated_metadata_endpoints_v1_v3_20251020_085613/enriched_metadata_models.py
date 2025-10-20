class EnrichedMetadataResponse(BaseModel):
    """Enriched metadata extraction response v3.0.0 (45 fields)"""

    # ========================================================================
    # Core metadata (v2 compatible - REQUIRED)
    # ========================================================================
    keywords: str = Field(description="Comma-separated keywords (5-10)")
    topics: str = Field(description="Comma-separated topics (2-5)")
    questions: str = Field(description="Semicolon-separated questions (2-5)")
    summary: str = Field(description="Brief text summary (1-2 sentences)")

    # ========================================================================
    # Named entities (5 fields - OPTIONAL)
    # ========================================================================
    entities: Optional[str] = Field(default=None, description="All entities mentioned")
    person_names: Optional[str] = Field(default=None, description="Person names")
    organization_names: Optional[str] = Field(default=None, description="Organization names")
    location_names: Optional[str] = Field(default=None, description="Location names")
    product_names: Optional[str] = Field(default=None, description="Product names")

    # ========================================================================
    # Temporal information (3 fields - OPTIONAL)
    # ========================================================================
    dates: Optional[str] = Field(default=None, description="All dates found")
    date_earliest: Optional[str] = Field(default=None, description="Earliest date (ISO 8601)")
    date_latest: Optional[str] = Field(default=None, description="Latest date (ISO 8601)")

    # ========================================================================
    # Classification (4 fields - OPTIONAL)
    # ========================================================================
    categories: Optional[str] = Field(default=None, description="Comma-separated categories")
    language: Optional[str] = Field(default="en", description="Language code (ISO 639-1)")
    sentiment: Optional[str] = Field(default=None, description="positive | negative | neutral")
    document_type: Optional[str] = Field(default="other", description="product | invoice | contract | manual | article | other")

    # ========================================================================
    # Product/E-commerce (12 fields - OPTIONAL)
    # ========================================================================
    brand: Optional[str] = Field(default=None, description="Product brand")
    manufacturer: Optional[str] = Field(default=None, description="Manufacturer name")
    model: Optional[str] = Field(default=None, description="Product model")
    sku: Optional[str] = Field(default=None, description="Stock keeping unit")
    price: Optional[float] = Field(default=None, description="Product price (numeric)")
    currency: Optional[str] = Field(default=None, description="Currency code (USD, EUR, etc.)")
    year: Optional[int] = Field(default=None, description="Product year")
    color: Optional[str] = Field(default=None, description="Product color")
    size: Optional[str] = Field(default=None, description="Product size")
    weight: Optional[str] = Field(default=None, description="Product weight with unit")
    dimensions: Optional[str] = Field(default=None, description="Product dimensions")
    specifications: Optional[str] = Field(default=None, description="Key specifications")

    # ========================================================================
    # Business/Financial (8 fields - OPTIONAL)
    # ========================================================================
    vendor_name: Optional[str] = Field(default=None, description="Vendor name")
    vendor_id: Optional[str] = Field(default=None, description="Vendor ID")
    amount: Optional[float] = Field(default=None, description="Total amount (numeric)")
    tax_amount: Optional[float] = Field(default=None, description="Tax amount (numeric)")
    invoice_number: Optional[str] = Field(default=None, description="Invoice number")
    transaction_date: Optional[str] = Field(default=None, description="Transaction date (ISO 8601)")
    payment_method: Optional[str] = Field(default=None, description="Payment method")
    payment_status: Optional[str] = Field(default=None, description="Payment status")

    # ========================================================================
    # Technical/Metadata (6 fields - OPTIONAL)
    # ========================================================================
    technical_terms: Optional[str] = Field(default=None, description="Technical terms found")
    key_numbers: Optional[str] = Field(default=None, description="Important numbers")
    urls: Optional[str] = Field(default=None, description="URLs found")
    emails: Optional[str] = Field(default=None, description="Email addresses found")
    phone_numbers: Optional[str] = Field(default=None, description="Phone numbers found")
    confidence_score: Optional[float] = Field(default=0.0, description="Extraction confidence (0.0-1.0)")

    # ========================================================================
    # Processing metadata (REQUIRED)
    # ========================================================================
    chunk_id: Optional[str] = Field(default=None, description="Chunk identifier")
    model_used: str = Field(description="Model used for extraction")
    processing_time_ms: float = Field(description="Processing time in milliseconds")
    api_version: str = Field(default=API_VERSION, description="API version")

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                # Core metadata
                "keywords": "Apple, iPhone 15 Pro, smartphone, 5G, premium",
                "topics": "Consumer Electronics, Mobile Technology, Apple Products",
                "questions": "What is iPhone 15 Pro?, How much does it cost?, What are its specifications?",
                "summary": "Description of Apple iPhone 15 Pro with A17 Pro chip, 48MP camera, and titanium design.",

                # Named entities
                "entities": "Apple, iPhone 15 Pro, Foxconn, USA",
                "person_names": "",
                "organization_names": "Apple Inc., Foxconn Technology Group",
                "location_names": "USA, China",
                "product_names": "iPhone 15 Pro",

                # Temporal
                "dates": "2024-03, 2024",
                "date_earliest": "2024-03-01",
                "date_latest": "2024-03-31",

                # Classification
                "categories": "Electronics, Smartphones, Apple",
                "language": "en",
                "sentiment": "positive",
                "document_type": "product",

                # Product/E-commerce
                "brand": "Apple",
                "manufacturer": "Foxconn Technology Group",
                "model": "iPhone 15 Pro",
                "sku": "MHJA3LL/A",
                "price": 999.0,
                "currency": "USD",
                "year": 2024,
                "color": "Natural Titanium",
                "size": "128GB",
                "weight": "187g",
                "dimensions": "146.6 x 70.6 x 8.25 mm",
                "specifications": "A17 Pro chip, 48MP camera, 120Hz display",

                # Business/Financial
                "vendor_name": "Apple Store",
                "vendor_id": "",
                "amount": 999.0,
                "tax_amount": 79.92,
                "invoice_number": "",
                "transaction_date": "2024-03-15",
                "payment_method": "",
                "payment_status": "",

                # Technical
                "technical_terms": "A17 Pro, 48MP, 120Hz, 5G",
                "key_numbers": "999, 128, 187, 48",
                "urls": "",
                "emails": "",
                "phone_numbers": "",
                "confidence_score": 0.95,

                # Processing metadata
                "chunk_id": "chunk_001",
                "model_used": "32B-fast",
                "processing_time_ms": 850.5,
                "api_version": "3.0.0"
            }
        }
    }

class BatchMetadataResponse(BaseModel):
    """Batch metadata extraction response (v2 compatible)"""
    results: List[MetadataResponse]
    total_chunks: int
    successful: int
    failed: int
    total_processing_time_ms: float
    api_version: str = Field(default=API_VERSION)

class EnrichedBatchMetadataResponse(BaseModel):
    """Enriched batch metadata extraction response v3.0.0"""
    results: List[EnrichedMetadataResponse]
    total_chunks: int
    successful: int
    failed: int
    total_processing_time_ms: float
    api_version: str = Field(default=API_VERSION)

# ============================================================================
# Health & Version Models
# ============================================================================
