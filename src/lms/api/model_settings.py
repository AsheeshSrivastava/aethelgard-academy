"""Routes for the model provider Settings page (SPEC-17 section 6).

No route returns, accepts or logs a key: `key_set` is the only thing said about one.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lms.adapters.ai.providers.router import (
    KeyMissing,
    PaidNotConfirmed,
    ProviderRouter,
    UnknownProfile,
)


class SwitchRequest(BaseModel):
    profile_id: str
    confirm_paid: bool = False


def _problem(status: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"type": "about:blank", "title": title, "status": status, "detail": detail},
        media_type="application/problem+json",
    )


def model_settings_routes(router: ProviderRouter, learner_dependency: Any) -> APIRouter:
    api = APIRouter(prefix="/api/v1/settings/models", tags=["settings"])

    def overview() -> Dict[str, Any]:
        profiles = []
        for p in router.profiles.values():
            profiles.append(
                {
                    "id": p.id,
                    "label": p.label,
                    "kind": p.kind.value,
                    "base_url": p.base_url,
                    "model": p.model,
                    "paid": p.paid,
                    "price_per_million": p.price_per_million.model_dump() if p.price_per_million else None,
                    "estimate_per_question_usd": p.estimate_per_question_usd(),
                    "key_env": p.key_env,
                    "key_set": router.key_set(p),
                }
            )
        return {
            "profiles": profiles,
            "active": router.active_profile().id,
            "mock": router.mock,
            "cap_usd": router.cap_usd,
            "month_spend_usd": router.store.month_spend(),
        }

    @api.get("")
    def get_models(_: str = Depends(learner_dependency)):
        return overview()

    @api.put("/active")
    def put_active(body: SwitchRequest, _: str = Depends(learner_dependency)):
        if router.mock:
            return _problem(409, "Mock mode", "Mock mode is on (MOCK_AI=true); switching is disabled.")
        try:
            router.switch(body.profile_id, body.confirm_paid)
        except UnknownProfile:
            return _problem(404, "Unknown profile", f"No profile named '{body.profile_id}'.")
        except KeyMissing as exc:
            return _problem(409, "Key not set", str(exc))
        except PaidNotConfirmed:
            return _problem(409, "Confirmation needed", "A paid provider needs confirm_paid: true.")
        return overview()

    @api.post("/test")
    def post_test(_: str = Depends(learner_dependency)):
        return router.test_connection()

    @api.get("/usage")
    def get_usage(_: str = Depends(learner_dependency)):
        return {
            "session_id": router.store.session_id,
            "session": [asdict(t) for t in router.store.totals("session")],
            "month": [asdict(t) for t in router.store.totals("month")],
            "month_spend_usd": router.store.month_spend(),
            "cap_usd": router.cap_usd,
        }

    return api
