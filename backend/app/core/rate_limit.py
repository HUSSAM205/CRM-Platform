from slowapi import Limiter
from slowapi.util import get_remote_address

# In-process, per-IP rate limiting. Fine for a single-instance deployment; a
# multi-instance production deployment would need a shared backend (e.g. Redis)
# for the limiter state to be consistent across processes.
limiter = Limiter(key_func=get_remote_address)
