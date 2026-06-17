"""Pydantic records for OpenClaw action checks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["low", "medium", "high", "critical"]
DecisionName = Literal["allow", "warn", "defer", "block"]


class StrictRecord(BaseModel):
    """Base model with deterministic validation for public JSON records."""

    model_config = ConfigDict(extra="forbid")


class OpenClawActionProposal(StrictRecord):
    schema_version: str = "0.1.0"
    proposal_id: str
    phase: Literal["pre_action"] = "pre_action"
    agent_id: str | None = None
    session_id: str | None = None
    action_kind: str
    tool_name: str | None = None
    summary: str
    raw_agent_text: str | None = None
    tool_arguments: dict[str, object] = Field(default_factory=dict)
    external_effect: bool
    risk_level: RiskLevel
    evidence_refs: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    rollback_plan: str | None = None
    requires_human_confirmation: bool


class OpenClawResultClaim(StrictRecord):
    schema_version: str = "0.1.0"
    claim_id: str
    phase: Literal["post_action"] = "post_action"
    agent_id: str | None = None
    action_kind: str
    claimed_result: str
    evidence_refs: list[str] = Field(default_factory=list)
    logs_refs: list[str] = Field(default_factory=list)
    rollback_available: bool
    unresolved_items: list[str] = Field(default_factory=list)


class OpenClawMemoryWrite(StrictRecord):
    schema_version: str = "0.1.0"
    memory_id: str
    phase: Literal["memory_write"] = "memory_write"
    agent_id: str | None = None
    content: str
    claim_type: Literal["fact", "preference", "plan", "hypothesis", "unknown"]
    evidence_refs: list[str] = Field(default_factory=list)
    should_be_persistent: bool
    risk_level: RiskLevel


class OpenClawSkillInstall(StrictRecord):
    schema_version: str = "0.1.0"
    install_id: str
    phase: Literal["skill_install"] = "skill_install"
    agent_id: str | None = None
    skill_name: str
    source_ref: str | None = None
    requested_permissions: list[str] = Field(default_factory=list)
    install_steps: list[str] = Field(default_factory=list)
    network_required: bool
    shell_required: bool
    file_write_required: bool
    credential_access_required: bool
    risk_level: RiskLevel


class PicDiagnostics(StrictRecord):
    agent_tasks: list[str] = Field(default_factory=list)
    route_execution_requests: list[str] = Field(default_factory=list)
    residual_ledger: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)


class BridgeDecision(StrictRecord):
    schema_version: str = "0.1.0"
    decision_id: str
    input_ref: str
    phase: str
    decision: DecisionName
    allowed_to_execute: bool
    requires_human_review: bool
    pic_used: bool
    pic_accepted: bool | None = None
    pic_operationally_usable: bool | None = None
    pic_settled: bool | None = None
    missing_obligations: list[str] = Field(default_factory=list)
    residual_summary: dict[str, float] = Field(default_factory=dict)
    pic_diagnostics: PicDiagnostics = Field(default_factory=PicDiagnostics)
    safe_next_steps: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    safety_boundary: list[str] = Field(default_factory=list)


InputRecord = (
    OpenClawActionProposal | OpenClawResultClaim | OpenClawMemoryWrite | OpenClawSkillInstall
)
