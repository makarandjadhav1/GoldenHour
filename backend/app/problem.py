"""RFC 7807 error responses. The detail never echoes user input."""

from fastapi.responses import JSONResponse


def problem(status: int, code: str, title: str, detail: str, req_id: str = "") -> JSONResponse:
    """RFC 7807. The detail never echoes user input."""
    return JSONResponse(
        {
            "type": f"https://goldenhour.example/errors/{code}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": req_id,
        },
        status_code=status,
        media_type="application/problem+json",
    )
