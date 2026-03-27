import urllib.request
import urllib.parse
import json
from typing import Optional
from .errors import VisageAPIError, VisageAuthError, VisageLicenseNotFoundError
from .types import (
    LicenseVerifyResponse, RightsSummary,
    UsageEventResponse, Model, License, Deal, PaginatedResponse
)

DEFAULT_BASE_URL = "https://visagelabs.net/api"


class Visage:
    """
    Visage B2B API client.

    Example:
        from visage import Visage

        client = Visage(api_key="vsg_live_xxx")
        result = client.verify_license("VSG-A1B2-C3D4-E5F6")
        print(result.status)  # "ACTIVE"
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        if not api_key:
            raise ValueError("Visage: api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: dict = None, request_id: str = None) -> dict:
        url = self.base_url + path
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if request_id:
            headers["X-Request-Id"] = request_id

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {}
            msg = payload.get("error", str(e))
            req_id = payload.get("request_id", request_id)
            if e.code == 401:
                raise VisageAuthError(msg, req_id)
            if e.code == 404:
                raise VisageLicenseNotFoundError(msg, req_id)
            raise VisageAPIError(msg, e.code, req_id)

    # ── Public methods ─────────────────────────────────────────────

    def verify_license(self, license_key: str, request_id: str = None) -> LicenseVerifyResponse:
        """Verify a license key and retrieve its status and rights summary."""
        encoded = urllib.parse.quote(license_key)
        data = self._request("GET", f"/b2b-v1-verify-license?license_key={encoded}", request_id=request_id)
        rs = data.get("rights_summary", {})
        return LicenseVerifyResponse(
            status=data["status"],
            license_key=data["license_key"],
            model_sku=data.get("model_sku"),
            issued_at=data["issued_at"],
            deal_created_at=data["deal_created_at"],
            buyer_org_name=data["buyer_org_name"],
            talent_name=data["talent_name"],
            model_id=data.get("model_id"),
            agency_id=data.get("agency_id"),
            rights_summary=RightsSummary(
                media_types=rs.get("media_types", []),
                channels=rs.get("channels", []),
                geography=rs.get("geography", ""),
                duration=rs.get("duration", ""),
                derivatives_allowed=rs.get("derivatives_allowed", False),
                synthetic_reuse_allowed=rs.get("synthetic_reuse_allowed", False),
                training_allowed=rs.get("training_allowed", False),
                training_scope=rs.get("training_scope"),
                political_allowed=rs.get("political_allowed", False),
                adult_allowed=rs.get("adult_allowed", False),
                competitor_exclusion=rs.get("competitor_exclusion"),
            ),
            request_id=data.get("request_id", ""),
        )

    def log_usage(
        self,
        license_key: str = None,
        license_id: str = None,
        platform_id: str = None,
        event_type: str = "generation",
        model_id: str = None,
        asset_id: str = None,
        units: int = 1,
        metadata: dict = None,
        request_id: str = None,
    ) -> UsageEventResponse:
        """Log a usage event against a license."""
        body = {
            "platform_id": platform_id,
            "event_type": event_type,
            "units": units,
        }
        if license_key:
            body["license_key"] = license_key
        if license_id:
            body["license_id"] = license_id
        if model_id:
            body["model_id"] = model_id
        if asset_id:
            body["asset_id"] = asset_id
        if metadata:
            body["metadata"] = metadata

        data = self._request("POST", "/b2b-v1-usage-event", body=body, request_id=request_id)
        d = data.get("data", data)
        return UsageEventResponse(
            id=d["id"],
            license_id=d["license_id"],
            units=d["units"],
            platform_id=d.get("platform_id"),
            event_type=d["event_type"],
            model_id=d.get("model_id"),
            asset_id=d.get("asset_id"),
            metadata=d.get("metadata"),
            created_at=d["created_at"],
            request_id=data.get("meta", {}).get("request_id", ""),
        )

    def list_models(self, limit: int = 20, offset: int = 0, sku: str = None, request_id: str = None) -> PaginatedResponse:
        """List available model profiles."""
        params = {"limit": limit, "offset": offset}
        if sku:
            params["sku"] = sku
        qs = urllib.parse.urlencode(params)
        data = self._request("GET", f"/b2b-v1-models?{qs}", request_id=request_id)
        return PaginatedResponse(
            data=[Model(**{k: m.get(k) for k in Model.__dataclass_fields__}) for m in data.get("data", [])],
            total=data.get("meta", {}).get("total", 0),
            limit=data.get("meta", {}).get("limit", limit),
            offset=data.get("meta", {}).get("offset", offset),
            request_id=data.get("meta", {}).get("request_id", ""),
        )

    def get_model_by_sku(self, sku: str, request_id: str = None) -> Model:
        """Retrieve a single model by SKU."""
        result = self.list_models(sku=sku, request_id=request_id)
        if not result.data:
            raise VisageLicenseNotFoundError(f"Model with SKU '{sku}' not found")
        return result.data[0]

    def list_licenses(self, status: str = None, limit: int = 20, offset: int = 0, request_id: str = None) -> PaginatedResponse:
        """List all licenses for your organisation."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        qs = urllib.parse.urlencode(params)
        data = self._request("GET", f"/b2b-v1-licenses?{qs}", request_id=request_id)
        return PaginatedResponse(
            data=[License(**{k: l.get(k) for k in License.__dataclass_fields__}) for l in data.get("data", [])],
            total=data.get("meta", {}).get("total", 0),
            limit=data.get("meta", {}).get("limit", limit),
            offset=data.get("meta", {}).get("offset", offset),
            request_id=data.get("meta", {}).get("request_id", ""),
        )

    def list_deals(self, status: str = None, limit: int = 20, offset: int = 0, request_id: str = None) -> PaginatedResponse:
        """List all deals for your organisation."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        qs = urllib.parse.urlencode(params)
        data = self._request("GET", f"/b2b-v1-deals?{qs}", request_id=request_id)
        return PaginatedResponse(
            data=[Deal(**{k: d.get(k) for k in Deal.__dataclass_fields__}) for d in data.get("data", [])],
            total=data.get("meta", {}).get("total", 0),
            limit=data.get("meta", {}).get("limit", limit),
            offset=data.get("meta", {}).get("offset", offset),
            request_id=data.get("meta", {}).get("request_id", ""),
        )
