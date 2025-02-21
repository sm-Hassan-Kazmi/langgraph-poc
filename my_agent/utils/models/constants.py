import os


DEFAULT_MAX_LISTINGS = 5
SESSION_KEY_PREFIX = "har-ai-labs:chatbot:session-data:"
CHAT_HISTORY_KEY_PREFIX = "har-ai-labs:chatbot:chat-history:{assistant}:"
API_CALL_LIMITTER_PREFIX = "har-ai-labs:chatbot:rate_limit:"
TTL_ONE_DAY = 86400  # 1 day in seconds
GPT35_MAX_TOKENS = 16385

# tools json response take ~900 tokens
# tools text response take ~650 tokens
# human question take ~100 tokens
# function call take ~500 tokens
TOKEN_THRESHOLD = GPT35_MAX_TOKENS - 6000
LLM_MODEL = "gpt-3.5-turbo"

# Redis URL
environment = os.getenv("DEV_ENVIRONMENT")
if environment == "localhost":
    REDIS_URL = "redis://default:mypassword@localhost:6379"
elif environment == "localhost_docker":
    REDIS_URL = "redis://default:mypassword@redis-stack:6379"
else:
    REDIS_URL = os.getenv("REDIS_URL")

# API Status Codes
API_SUCCESS_CODE = 200
API_CODE_UNAUTHORIZED = 401
API_CODE_BAD_REQUEST = 400
API_CODE_NOT_FOUND = 404
API_SERVER_ERROR = 500
API_CODE_LIMIT_EXCEEDED = 429
