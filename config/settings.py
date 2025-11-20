from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="DocumentClassifierAgent", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Groq API
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    groq_text_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_TEXT_MODEL")
    groq_vision_model: str = Field(default="meta-llama/llama-4-scout-17b-16e-instruct", env="GROQ_VISION_MODEL")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # File System
    input_folder: str = Field(default="./input_pdfs", env="INPUT_FOLDER")
    output_base_folder: str = Field(default="./output", env="OUTPUT_BASE_FOLDER")
    temp_folder: str = Field(default="/tmp/document_processing", env="TEMP_FOLDER")
    
    # MCP
    mcp_server_host: str = Field(default="localhost", env="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8001, env="MCP_SERVER_PORT")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # Frontend
    streamlit_server_address: str = Field(default="0.0.0.0", env="API_HOST")
    streamlit_server_port: int = Field(default=8501, env="API_PORT")
    
    # Processing
    max_pages_per_document: int = Field(default=100, env="MAX_PAGES_PER_DOCUMENT")
    batch_size: int = Field(default=5, env="BATCH_SIZE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Domain mapping configuration
DOMAIN_KEYWORDS = {
    "finance": [
        "financial", "banking", "investment", "stock", "bond", "portfolio",
        "accounting", "audit", "revenue", "profit", "loss", "balance sheet",
        "income statement", "cash flow", "equity", "asset", "liability",
        "fiscal", "monetary", "securities", "derivatives", "hedge fund"
    ],
    "law": [
        "legal", "court", "judge", "attorney", "lawsuit", "plaintiff",
        "defendant", "verdict", "statute", "regulation", "compliance",
        "contract", "agreement", "litigation", "jurisdiction", "appeal",
        "prosecution", "defense", "testimony", "evidence", "judicial"
    ],
    "science": [
        "research", "experiment", "hypothesis", "theory", "methodology",
        "analysis", "data", "results", "conclusion", "abstract", "publication",
        "peer review", "scientific", "laboratory", "variable", "control",
        "observation", "phenomenon", "empirical", "quantitative"
    ],
    "technology": [
        "software", "hardware", "algorithm", "programming", "code",
        "system", "application", "platform", "network", "database",
        "cloud", "artificial intelligence", "machine learning", "cybersecurity",
        "blockchain", "api", "framework", "architecture", "deployment"
    ],
    "healthcare": [
        "medical", "patient", "diagnosis", "treatment", "clinical",
        "hospital", "physician", "nurse", "therapy", "medication",
        "disease", "symptom", "health", "care", "surgical", "pharmaceutical",
        "radiology", "pathology", "anatomy", "physiology"
    ],
    "education": [
        "teaching", "learning", "student", "curriculum", "course",
        "pedagogy", "instruction", "assessment", "academic", "university",
        "school", "education", "training", "classroom", "textbook",
        "syllabus", "enrollment", "degree", "diploma", "scholarship"
    ],
    "business": [
        "management", "strategy", "marketing", "sales", "customer",
        "product", "service", "business plan", "entrepreneurship", "startup",
        "operations", "supply chain", "vendor", "procurement", "logistics",
        "human resources", "employee", "organizational", "corporate"
    ],
    "engineering": [
        "design", "construction", "structural", "mechanical", "electrical",
        "civil", "chemical", "aerospace", "manufacturing", "CAD",
        "blueprint", "specifications", "materials", "testing", "prototype",
        "maintenance", "installation", "inspection", "quality control"
    ],
    "arts": [
        "creative", "artistic", "design", "visual", "performance",
        "music", "theater", "literature", "painting", "sculpture",
        "photography", "film", "media", "aesthetic", "exhibition",
        "gallery", "composition", "choreography", "narrative"
    ]
}


# Ensure directories exist
def setup_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(settings.input_folder, exist_ok=True)
    os.makedirs(settings.output_base_folder, exist_ok=True)
    os.makedirs(settings.temp_folder, exist_ok=True)
    
    # Create domain-specific folders
    for domain in DOMAIN_KEYWORDS.keys():
        domain_folder = os.path.join(settings.output_base_folder, domain)
        os.makedirs(domain_folder, exist_ok=True)
    
    # Create general folder
    general_folder = os.path.join(settings.output_base_folder, "general")
    os.makedirs(general_folder, exist_ok=True)