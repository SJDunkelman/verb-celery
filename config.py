from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv( Path(__file__).parent.parent / '.env')

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY: str = os.environ.get("SUPABASE_ANON_KEY")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY")

LIX_API_KEY: str = os.getenv("LIX_API_KEY")

REDIS_URL: str = os.getenv('REDIS_URL')
CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")

ROOT_DIR = Path(__file__).parent
NLP_SERVICE_DIR = ROOT_DIR / "nlp_service"
