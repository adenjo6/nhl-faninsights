"""gRPC client for the prospect-service (Go microservice).

The browser never speaks gRPC: this client is the gateway's only door to the
Go service. It owns a single, lazily-connecting channel reused across requests
(grpc channels are thread-safe, which matters because the prospects routes run
on FastAPI's sync threadpool).

House pattern for optional integrations: if ``PROSPECT_SERVICE_ADDR`` is unset
the client is "disabled" and every call soft-fails (list -> None, get ->
ProspectServiceUnavailable) rather than raising on import or at startup. The
same soft-fail covers transport errors (service down / deadline exceeded) so a
prospect-service outage degrades the feature instead of breaking the API.
"""
import logging

import grpc

import app.grpc_gen  # noqa: F401  — side effect: puts grpc_gen on sys.path
from prospects.v1 import prospects_pb2 as pb2
from prospects.v1 import prospects_pb2_grpc as pb2_grpc
from app.config import settings

logger = logging.getLogger(__name__)


class ProspectServiceUnavailable(Exception):
    """Raised when the prospect-service is unreachable or not configured."""


class ProspectNotFound(Exception):
    """Raised when the prospect-service reports NOT_FOUND for a given id."""


class ProspectClient:
    """Thin wrapper around the generated ProspectServiceStub."""

    def __init__(self) -> None:
        self._channel: grpc.Channel | None = None
        self._stub: pb2_grpc.ProspectServiceStub | None = None

    def connect(self) -> None:
        """Create the gRPC channel. Called once from the app lifespan.

        ``insecure_channel`` is lazy — it does not dial until the first RPC — so
        this never fails even if the service is down; the per-call deadline on
        each RPC handles unavailability instead.
        """
        addr = settings.PROSPECT_SERVICE_ADDR
        if not addr:
            logger.info("prospect-service disabled (PROSPECT_SERVICE_ADDR unset)")
            return
        self._channel = grpc.insecure_channel(addr)
        self._stub = pb2_grpc.ProspectServiceStub(self._channel)
        logger.info("✓ prospect-service client configured: %s", addr)

    def close(self) -> None:
        """Close the channel on shutdown."""
        if self._channel is not None:
            self._channel.close()
            self._channel = None
            self._stub = None

    @property
    def enabled(self) -> bool:
        return self._stub is not None

    def list_prospects(self, position: str | None, league: str | None):
        """Return a list of Prospect protos, or None if the service is
        unavailable/disabled.

        None (not []) signals "couldn't reach the service" so the caller can
        soft-fail without caching the empty result. An empty list means the
        service genuinely returned no prospects and is safe to cache.
        """
        if self._stub is None:
            return None
        req = pb2.ListProspectsRequest(position=position or "", league=league or "")
        try:
            resp = self._stub.ListProspects(req, timeout=settings.PROSPECT_SERVICE_TIMEOUT)
            return list(resp.prospects)
        except grpc.RpcError as exc:
            logger.warning("prospect-service ListProspects failed: %s", _rpc_detail(exc))
            return None

    def get_prospect(self, prospect_id: int):
        """Return a single Prospect proto.

        Raises ProspectNotFound (NOT_FOUND) or ProspectServiceUnavailable
        (disabled / transport error) — the caller maps these to 404 / 503.
        """
        if self._stub is None:
            raise ProspectServiceUnavailable("prospect-service not configured")
        req = pb2.GetProspectRequest(id=prospect_id)
        try:
            resp = self._stub.GetProspect(req, timeout=settings.PROSPECT_SERVICE_TIMEOUT)
            return resp.prospect
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                raise ProspectNotFound(str(prospect_id)) from exc
            logger.warning("prospect-service GetProspect failed: %s", _rpc_detail(exc))
            raise ProspectServiceUnavailable(_rpc_detail(exc)) from exc


def _rpc_detail(exc: grpc.RpcError) -> str:
    """Best-effort code/details string from an RpcError for logging."""
    try:
        return f"{exc.code().name}: {exc.details()}"
    except Exception:  # pragma: no cover — defensive
        return str(exc)


# Module-level singleton, wired into the app lifespan in app/main.py.
prospect_client = ProspectClient()
