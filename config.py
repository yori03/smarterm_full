import os

from dotenv import load_dotenv

load_dotenv()

# --- JWT ---
SECRET_KEY = os.getenv("SECRET_KEY", "ganti_ini_di_env_ya")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

# --- Database ---
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "db_smarterm")

# --- Groq AI ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")