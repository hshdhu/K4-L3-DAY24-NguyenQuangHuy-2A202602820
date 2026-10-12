"""BƯỚC 3b — PEP (Policy Enforcement Point) tại tool call (15').

Cổng chặn TRƯỚC KHI tool thật sự execute. Đọc CHECKPOINTS.md (§3b).

Interface bắt buộc (tests/test_policy.py và agent/runner.py gọi trực tiếp):

    check(context: PolicyContext) -> tuple[bool, str]
        Trả về (allow, reason).
        `reason` KHÔNG BAO GIỜ được để trống — cả khi allow=True và
        allow=False. Đây là evidence audit ở Bước 4 (rubric: "Audit
        completeness = 100%" — điều kiện trượt nếu có dòng thiếu reason).

PolicyContext — 5 input gốc và các input OBO cho lớp L3:

    data_classification: str   "public" | "internal" | "restricted"
    request_purpose: str       tự do, ví dụ "reconciliation", "support-reply"
    agent_owner: str            định danh agent/run gọi tool này
    delegation_depth: int       0 = gọi trực tiếp bởi user, >0 = agent gọi agent
    egress_enabled: bool        run hiện tại có được phép gọi network không
    principal_id: str           ID người ra lệnh từ data/principals.json
    requested_tool: str         tool sắp gọi
    agent_scopes: tuple[str]    quyền tối đa của agent
    parent_scopes: tuple[str]   quyền của agent cha khi delegation_depth > 0
    expires_at: str             ISO-8601 UTC; hết hạn phải deny

Rule TỐI THIỂU bắt buộc (không được viết yếu hơn rule này):

    classification == "restricted" and egress_enabled is True  ->  DENY

Checkpoint OBO: quyền hiệu lực = principal.allowed_tools ∩ agent_scopes,
và nếu depth > 0 thì còn giao với parent_scopes. Unknown principal, scope
thiếu, run hết hạn đều deny kèm reason. Principal là fixture mô phỏng,
không phải xác thực người dùng production.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path


PRINCIPALS_FILE = Path(__file__).resolve().parent.parent / "data" / "principals.json"


@dataclass(frozen=True)
class PolicyContext:
    data_classification: str
    request_purpose: str
    agent_owner: str
    delegation_depth: int
    egress_enabled: bool
    principal_id: str = ""
    requested_tool: str = ""
    agent_scopes: tuple[str, ...] = ()
    parent_scopes: tuple[str, ...] = ()
    expires_at: str = ""


def check(context: PolicyContext) -> tuple[bool, str]:
    if context.data_classification not in {"public", "internal", "restricted"}:
        return False, "Unknown data classification"
    if context.data_classification == "restricted" and context.egress_enabled:
        return False, "Restricted data cannot be used in a run with egress enabled"

    try:
        principals = json.loads(PRINCIPALS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "Cannot load principal permissions"
    if not isinstance(principals, dict):
        return False, "Invalid principal permissions"
    principal = principals.get(context.principal_id)
    if not isinstance(principal, dict):
        return False, "Unknown principal"

    if not context.agent_owner or context.delegation_depth < 0:
        return False, "Missing agent owner or invalid delegation depth"
    if context.request_purpose not in principal.get("purposes", []):
        return False, "Request purpose is not permitted for this principal"
    if context.requested_tool not in principal.get("allowed_tools", []):
        return False, "Requested tool is not permitted for this principal"
    if context.requested_tool not in context.agent_scopes:
        return False, "Requested tool is outside agent scopes"
    if context.delegation_depth > 0 and context.requested_tool not in context.parent_scopes:
        return False, "Requested tool is outside parent scopes"

    try:
        expires_at = datetime.fromisoformat(context.expires_at)
    except (TypeError, ValueError):
        return False, "Invalid expiry timestamp"
    if expires_at.tzinfo is None or expires_at.utcoffset() != timedelta(0):
        return False, "Expiry timestamp must include UTC timezone"
    if expires_at <= datetime.now(timezone.utc):
        return False, "Agent permissions have expired"

    return True, "Classification, principal, purpose, scopes and UTC expiry are valid"
