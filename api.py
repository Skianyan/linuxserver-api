from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import subprocess

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

app = FastAPI()

# rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate limit exceeded"}
    )


class CommandRequest(BaseModel):
    command: str
    params: list[str] = []


ALLOWED = {
    "uptime": ["/usr/bin/uptime"],
    "disk": ["/usr/bin/df", "-h"],
    "memory": ["/usr/bin/free", "-m"]
}


def execute(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode
    }


@app.post("/system/execute")
@limiter.limit("10/minute")
async def system_execute(request: Request, req: CommandRequest):

    if req.command not in ALLOWED:
        raise HTTPException(status_code=403, detail="command not allowed")

    base_cmd = ALLOWED[req.command]
    cmd = base_cmd + req.params

    return {
        "command": req.command,
        "params": req.params,
        "result": execute(cmd)
    }
