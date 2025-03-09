import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bank and Interview Data
BANKS = [
    "Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America",
    "Citigroup", "Credit Suisse", "Deutsche Bank", "Barclays", "UBS", "Wells Fargo"
]

COVERAGE_AREAS = [
    "Technology", "Healthcare", "Financial Institutions (FIG)", "Industrials",
    "Consumer & Retail", "Energy", "Real Estate", "Media & Telecommunications"
]

INTERVIEW_TYPES = ["Coffee Chat", "First Round", "Superday"]

INTERVIEW_TOPICS = {
    "Coffee Chat": [
        "Career Goals and Aspirations",
        "Interest in Investment Banking",
        "Understanding of the Role",
        "Bank Culture and Values",
        "Recent Market Events"
    ],
    "First Round": [
        "Basic Technical Questions",
        "Three Financial Statements",
        "Financial Modeling Experience",
        "Valuation Methods Overview",
        "Industry Knowledge"
    ],
    "Superday": [
        "Advanced Technical Questions",
        "Complex Valuation Methods (DCF, LBO, M&A)",
        "Deal Experience",
        "Market Analysis",
        "Leadership and Teamwork",
        "Client Interaction Scenarios"
    ]
}

INTERVIEW_PREP = {
    "Coffee Chat": {
        "Preparation Focus": [
            "Research recent news about the bank",
        ],
        "Attire": "Business casual or smart casual",
        "Duration": "30-45 minutes",
        "Key Tips": [
            "Show genuine interest and enthusiasm",
        ]
    },
}

# Email Configuration
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Zoom Configuration
ZOOM_ACCOUNT_ID = os.getenv('ZOOM_ACCOUNT_ID')
ZOOM_CLIENT_ID = os.getenv('ZOOM_CLIENT_ID')
ZOOM_CLIENT_SECRET = os.getenv('ZOOM_CLIENT_SECRET')
ZOOM_USER_ID = os.getenv('ZOOM_USER_ID')

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Resume Analysis Configuration
RESUME_ANALYSIS_CRITERIA = {
    "Format and Presentation": [
        "Clear section headers",
        "Consistent formatting",
        "Professional font and spacing",
        "One to two pages in length"
    ],
    "Technical Skills": [
        "Financial modeling",
        "Valuation methods",
        "Industry knowledge",
        "Excel and PowerPoint"
    ],
    "Banking-Specific Experience": [
        "Deal experience",
        "Financial analysis",
        "Client interaction",
        "Market research"
    ],
    "Quantitative Achievements": [
        "Deal sizes",
        "Project impacts",
        "Team leadership",
        "Revenue growth"
    ]
}

# Industry-specific keywords for each coverage area
COVERAGE_KEYWORDS = {
    "Technology": [
        "SaaS", "Cloud", "AI/ML", "Digital transformation",
        "Enterprise software", "Cybersecurity", "E-commerce"
    ],
    "Healthcare": [
        "Biotech", "Medical devices", "Healthcare IT",
        "Pharmaceuticals", "Clinical trials", "FDA regulations"
    ],
    "Financial Institutions (FIG)": [
        "Asset management", "Insurance", "Fintech",
        "Banking regulations", "Capital requirements", "Risk management"
    ],
} 