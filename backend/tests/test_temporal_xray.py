"""
Chitta Temporal Design X-Ray Test

This test file creates a comprehensive timeline transcript of the internal temporal design
processes during a realistic conversation. It captures:

1. EXPLORATION CYCLES
   - When cycles are created
   - Cycle status transitions (active -> evidence_gathering -> synthesizing -> complete)
   - Which domains each cycle focuses on

2. HYPOTHESES
   - Formation of new hypotheses
   - Theory/domain/source tracking
   - Confidence evolution with evidence
   - Status changes (forming -> active -> weakening -> resolved)
   - Resolution outcomes (confirmed, refuted, evolved, inconclusive)

3. EVIDENCE
   - Each piece of evidence captured
   - Source (conversation, video, parent_update)
   - Which hypotheses it affects
   - Effect on confidence (supports, contradicts, neutral, transforms)

4. ARTIFACTS
   - Video guidelines generation
   - When artifacts are created/updated
   - Artifact status (draft, ready, fulfilled, superseded, needs_update)

5. PATTERNS
   - Cross-cycle pattern detection
   - Themes emerging across multiple hypotheses

6. VIDEO WORKFLOW
   - When video observation is requested
   - Guidelines generation
   - (Would track upload/analysis if implemented)

Output Format:
- JSON timeline suitable for UI dashboard consumption
- Markdown report for human review
- Console output for real-time monitoring

Usage:
    python tests/test_temporal_xray.py [--output-dir DIR] [--scenario NAME]
"""

import requests
import json
import time
import argparse
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


# === Configuration ===

BASE_URL = "http://localhost:8000"
DEFAULT_OUTPUT_DIR = "/home/shlomi/projects/chitta/chitta-advanced/backend/tests/xray_outputs"


# === Event Types ===

class EventType(str, Enum):
    # Cycle events
    CYCLE_CREATED = "cycle_created"
    CYCLE_STATUS_CHANGED = "cycle_status_changed"
    CYCLE_COMPLETED = "cycle_completed"

    # Hypothesis events
    HYPOTHESIS_FORMED = "hypothesis_formed"
    HYPOTHESIS_EVIDENCE_ADDED = "hypothesis_evidence_added"
    HYPOTHESIS_CONFIDENCE_CHANGED = "hypothesis_confidence_changed"
    HYPOTHESIS_STATUS_CHANGED = "hypothesis_status_changed"
    HYPOTHESIS_RESOLVED = "hypothesis_resolved"

    # Artifact events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_STATUS_CHANGED = "artifact_status_changed"
    VIDEO_GUIDELINES_GENERATED = "video_guidelines_generated"
    VIDEO_UPLOADED = "video_uploaded"
    VIDEO_ANALYZED = "video_analyzed"

    # Pattern events
    PATTERN_DETECTED = "pattern_detected"

    # Insight events
    INSIGHT_QUEUED = "insight_queued"
    INSIGHT_SHARED = "insight_shared"

    # Tool events
    TOOL_CALLED = "tool_called"

    # Conversation events
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"


@dataclass
class TimelineEvent:
    """A single event in the timeline"""
    timestamp: str
    turn: int
    event_type: str
    category: str  # "cycle", "hypothesis", "artifact", "pattern", "insight", "tool", "conversation"
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    related_ids: Dict[str, str] = field(default_factory=dict)  # cycle_id, hypothesis_id, etc.


@dataclass
class TurnSnapshot:
    """Complete snapshot after each turn"""
    turn: int
    timestamp: str
    parent_message: str
    chitta_response: str
    events: List[TimelineEvent] = field(default_factory=list)

    # State snapshots
    child_profile: Dict[str, Any] = field(default_factory=dict)
    exploration_cycles: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses_summary: List[Dict[str, Any]] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)

    # Metrics
    completeness: float = 0.0
    active_cycles_count: int = 0
    hypotheses_count: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)

    # Conversation memory (from reflection)
    conversation_memory: Dict[str, Any] = field(default_factory=dict)

    # === Living Gestalt Fields ===
    # Full child gestalt data from /child/{family_id}/gestalt endpoint
    gestalt_identity: Dict[str, Any] = field(default_factory=dict)  # name, birth_date, gender
    gestalt_essence: Dict[str, Any] = field(default_factory=dict)  # temperament, energy_pattern, core_qualities
    gestalt_strengths: Dict[str, Any] = field(default_factory=dict)  # abilities, interests, what_lights_them_up
    gestalt_concerns: Dict[str, Any] = field(default_factory=dict)  # primary_areas, details, parent_narrative
    gestalt_history: Dict[str, Any] = field(default_factory=dict)  # birth, early_development, milestones
    gestalt_family: Dict[str, Any] = field(default_factory=dict)  # structure, siblings, languages
    gestalt_understanding: Dict[str, Any] = field(default_factory=dict)  # hypotheses, patterns (from understanding)
    gestalt_synthesis: List[Dict[str, Any]] = field(default_factory=list)  # synthesis reports


@dataclass
class XRayReport:
    """Complete X-Ray report"""
    session_id: str
    family_id: str
    generated_at: str
    scenario_name: str

    turns: List[TurnSnapshot] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)

    # Final state
    final_child_profile: Dict[str, Any] = field(default_factory=dict)
    final_cycles: List[Dict[str, Any]] = field(default_factory=list)
    final_patterns: List[Dict[str, Any]] = field(default_factory=list)

    # Analytics
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    hypotheses_formed: int = 0
    hypotheses_resolved: int = 0
    cycles_created: int = 0
    cycles_completed: int = 0
    artifacts_created: int = 0


class ChittaXRayTest:
    """X-Ray test runner that captures all internal events"""

    def __init__(self, base_url: str = BASE_URL, output_dir: str = DEFAULT_OUTPUT_DIR):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session_id = f"xray-{int(time.time())}"
        self.family_id = f"xray-test-{int(time.time())}"

        # State tracking for diff detection
        self._prev_cycles: Dict[str, Dict] = {}
        self._prev_hypotheses: Dict[str, Dict] = {}
        self._prev_artifacts: Dict[str, Dict] = {}
        self._prev_patterns: Dict[str, Dict] = {}

        # Error tracking
        self.errors: List[Dict[str, Any]] = []

        self.report = XRayReport(
            session_id=self.session_id,
            family_id=self.family_id,
            generated_at=datetime.now().isoformat(),
            scenario_name="default"
        )

    def _record_error(self, context: str, error: str, turn: Optional[int] = None, details: Optional[Dict] = None):
        """Record an error for visibility in report"""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error": error,
            "turn": turn,
            "details": details or {}
        }
        self.errors.append(error_record)
        print(f"  ⚠️  ERROR [{context}]: {error}")

    def send_message(self, message: str, turn: Optional[int] = None) -> Dict[str, Any]:
        """Send a message and return the full response with error handling"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat/v2/send",
                json={"family_id": self.family_id, "message": message},
                timeout=120
            )

            # Check HTTP status
            if resp.status_code != 200:
                self._record_error(
                    "send_message",
                    f"HTTP {resp.status_code}",
                    turn=turn,
                    details={"response_text": resp.text[:500] if resp.text else None}
                )
                return {"error": f"HTTP {resp.status_code}", "response": "", "ui_data": {}}

            data = resp.json()

            # Check for API-level errors in response
            if "error" in data:
                self._record_error(
                    "send_message",
                    data.get("error", "Unknown API error"),
                    turn=turn,
                    details=data
                )

            return data

        except requests.exceptions.Timeout:
            self._record_error("send_message", "Request timeout (120s)", turn=turn)
            return {"error": "timeout", "response": "", "ui_data": {}}
        except requests.exceptions.ConnectionError as e:
            self._record_error("send_message", f"Connection error: {e}", turn=turn)
            return {"error": "connection_error", "response": "", "ui_data": {}}
        except Exception as e:
            self._record_error("send_message", f"Unexpected error: {type(e).__name__}: {e}", turn=turn)
            return {"error": str(e), "response": "", "ui_data": {}}

    def get_child_data(self, turn: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get full child data including cycles, hypotheses, etc."""
        try:
            resp = requests.get(f"{self.base_url}/api/child/{self.family_id}", timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code != 404:  # 404 is expected for new sessions
                self._record_error(
                    "get_child_data",
                    f"HTTP {resp.status_code}",
                    turn=turn,
                    details={"response_text": resp.text[:500] if resp.text else None}
                )
            return None
        except Exception as e:
            self._record_error("get_child_data", f"{type(e).__name__}: {e}", turn=turn)
            return None

    def get_state(self, turn: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get internal state"""
        try:
            resp = requests.get(f"{self.base_url}/api/state/{self.family_id}", timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code != 404:
                self._record_error(
                    "get_state",
                    f"HTTP {resp.status_code}",
                    turn=turn,
                    details={"response_text": resp.text[:500] if resp.text else None}
                )
            return None
        except Exception as e:
            self._record_error("get_state", f"{type(e).__name__}: {e}", turn=turn)
            return None

    def get_session_memory(self, turn: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get session conversation memory (distilled from reflection)"""
        try:
            resp = requests.get(f"{self.base_url}/dev/session/{self.family_id}/memory", timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code != 404:
                self._record_error(
                    "get_session_memory",
                    f"HTTP {resp.status_code}",
                    turn=turn
                )
            return None
        except Exception as e:
            self._record_error("get_session_memory", f"{type(e).__name__}: {e}", turn=turn)
            return None

    def get_child_gestalt(self, turn: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get complete child gestalt data (Living Gestalt fields)"""
        try:
            resp = requests.get(f"{self.base_url}/api/child/{self.family_id}/gestalt", timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code != 404:
                self._record_error(
                    "get_child_gestalt",
                    f"HTTP {resp.status_code}",
                    turn=turn
                )
            return None
        except Exception as e:
            self._record_error("get_child_gestalt", f"{type(e).__name__}: {e}", turn=turn)
            return None

    def init_conversation(self, turn: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Initialize conversation and get Chitta's greeting (Turn 0)"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat/v2/init/{self.family_id}",
                json={},
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                self._record_error(
                    "init_conversation",
                    f"HTTP {resp.status_code}",
                    turn=turn,
                    details={"response_text": resp.text[:500] if resp.text else None}
                )
            return None
        except Exception as e:
            self._record_error("init_conversation", f"{type(e).__name__}: {e}", turn=turn)
            return None

    def _detect_events(self, turn: int, child_data: Dict, ui_data: Dict) -> List[TimelineEvent]:
        """Detect all events by comparing current state to previous state"""
        events = []
        ts = datetime.now().isoformat()

        # === Detect Tool Calls ===
        tool_calls = ui_data.get("tool_calls", [])
        for tc in tool_calls:
            events.append(TimelineEvent(
                timestamp=ts,
                turn=turn,
                event_type=EventType.TOOL_CALLED,
                category="tool",
                summary=f"Tool called: {tc.get('tool', 'unknown')}",
                details={
                    "tool": tc.get("tool"),
                    "arguments": tc.get("arguments", {}),
                    "result": tc.get("result", {})
                }
            ))

        # === Detect Cycle Events ===
        cycles = child_data.get("exploration_cycles", [])
        current_cycles = {c.get("id"): c for c in cycles}

        for cycle_id, cycle in current_cycles.items():
            prev_cycle = self._prev_cycles.get(cycle_id)

            if prev_cycle is None:
                # New cycle created
                events.append(TimelineEvent(
                    timestamp=ts,
                    turn=turn,
                    event_type=EventType.CYCLE_CREATED,
                    category="cycle",
                    summary=f"Exploration cycle created: {cycle.get('focus_domain', 'unknown')}",
                    details={
                        "focus_domain": cycle.get("focus_domain"),
                        "focus_description": cycle.get("focus_description"),
                        "status": cycle.get("status")
                    },
                    related_ids={"cycle_id": cycle_id}
                ))
                self.report.cycles_created += 1
            else:
                # Check status change
                if cycle.get("status") != prev_cycle.get("status"):
                    events.append(TimelineEvent(
                        timestamp=ts,
                        turn=turn,
                        event_type=EventType.CYCLE_STATUS_CHANGED,
                        category="cycle",
                        summary=f"Cycle status: {prev_cycle.get('status')} -> {cycle.get('status')}",
                        details={
                            "previous_status": prev_cycle.get("status"),
                            "new_status": cycle.get("status")
                        },
                        related_ids={"cycle_id": cycle_id}
                    ))

                    if cycle.get("status") == "complete":
                        events.append(TimelineEvent(
                            timestamp=ts,
                            turn=turn,
                            event_type=EventType.CYCLE_COMPLETED,
                            category="cycle",
                            summary=f"Cycle completed: {cycle.get('focus_domain')}",
                            details={"focus_domain": cycle.get("focus_domain")},
                            related_ids={"cycle_id": cycle_id}
                        ))
                        self.report.cycles_completed += 1

            # === Detect Hypothesis Events within cycles ===
            hypotheses = cycle.get("hypotheses", [])
            for hyp in hypotheses:
                hyp_id = hyp.get("id")
                prev_hyp = self._prev_hypotheses.get(hyp_id)

                if prev_hyp is None:
                    # New hypothesis formed
                    events.append(TimelineEvent(
                        timestamp=ts,
                        turn=turn,
                        event_type=EventType.HYPOTHESIS_FORMED,
                        category="hypothesis",
                        summary=f"Hypothesis formed: {hyp.get('theory', '')[:50]}...",
                        details={
                            "theory": hyp.get("theory"),
                            "domain": hyp.get("domain"),
                            "source": hyp.get("source"),
                            "initial_confidence": hyp.get("confidence", 0.5),
                            "questions_to_explore": hyp.get("questions_to_explore", [])
                        },
                        related_ids={"cycle_id": cycle_id, "hypothesis_id": hyp_id}
                    ))
                    self.report.hypotheses_formed += 1
                else:
                    # Check confidence change
                    if hyp.get("confidence") != prev_hyp.get("confidence"):
                        events.append(TimelineEvent(
                            timestamp=ts,
                            turn=turn,
                            event_type=EventType.HYPOTHESIS_CONFIDENCE_CHANGED,
                            category="hypothesis",
                            summary=f"Confidence: {prev_hyp.get('confidence', 0):.0%} -> {hyp.get('confidence', 0):.0%}",
                            details={
                                "previous_confidence": prev_hyp.get("confidence"),
                                "new_confidence": hyp.get("confidence"),
                                "theory": hyp.get("theory")
                            },
                            related_ids={"cycle_id": cycle_id, "hypothesis_id": hyp_id}
                        ))

                    # Check status change
                    if hyp.get("status") != prev_hyp.get("status"):
                        events.append(TimelineEvent(
                            timestamp=ts,
                            turn=turn,
                            event_type=EventType.HYPOTHESIS_STATUS_CHANGED,
                            category="hypothesis",
                            summary=f"Status: {prev_hyp.get('status')} -> {hyp.get('status')}",
                            details={
                                "previous_status": prev_hyp.get("status"),
                                "new_status": hyp.get("status"),
                                "theory": hyp.get("theory")
                            },
                            related_ids={"cycle_id": cycle_id, "hypothesis_id": hyp_id}
                        ))

                        if hyp.get("status") == "resolved":
                            events.append(TimelineEvent(
                                timestamp=ts,
                                turn=turn,
                                event_type=EventType.HYPOTHESIS_RESOLVED,
                                category="hypothesis",
                                summary=f"Hypothesis resolved: {hyp.get('resolution')}",
                                details={
                                    "resolution": hyp.get("resolution"),
                                    "resolution_note": hyp.get("resolution_note"),
                                    "final_confidence": hyp.get("confidence"),
                                    "theory": hyp.get("theory")
                                },
                                related_ids={"cycle_id": cycle_id, "hypothesis_id": hyp_id}
                            ))
                            self.report.hypotheses_resolved += 1

                    # Check for new evidence
                    prev_evidence_ids = {e.get("id") for e in prev_hyp.get("evidence", [])}
                    for evidence in hyp.get("evidence", []):
                        if evidence.get("id") not in prev_evidence_ids:
                            events.append(TimelineEvent(
                                timestamp=ts,
                                turn=turn,
                                event_type=EventType.HYPOTHESIS_EVIDENCE_ADDED,
                                category="hypothesis",
                                summary=f"Evidence added: {evidence.get('content', '')[:40]}...",
                                details={
                                    "content": evidence.get("content"),
                                    "source": evidence.get("source"),
                                    "domain": evidence.get("domain")
                                },
                                related_ids={"cycle_id": cycle_id, "hypothesis_id": hyp_id}
                            ))

                # Update prev hypotheses
                self._prev_hypotheses[hyp_id] = hyp

            # === Detect Artifact Events ===
            artifacts = cycle.get("artifacts", [])
            for artifact in artifacts:
                art_id = artifact.get("id")
                prev_art = self._prev_artifacts.get(art_id)

                if prev_art is None:
                    events.append(TimelineEvent(
                        timestamp=ts,
                        turn=turn,
                        event_type=EventType.ARTIFACT_CREATED,
                        category="artifact",
                        summary=f"Artifact created: {artifact.get('type')}",
                        details={
                            "type": artifact.get("type"),
                            "status": artifact.get("status"),
                            "related_hypothesis_ids": artifact.get("related_hypothesis_ids", [])
                        },
                        related_ids={"cycle_id": cycle_id, "artifact_id": art_id}
                    ))
                    self.report.artifacts_created += 1

                    if artifact.get("type") == "video_guidelines":
                        events.append(TimelineEvent(
                            timestamp=ts,
                            turn=turn,
                            event_type=EventType.VIDEO_GUIDELINES_GENERATED,
                            category="artifact",
                            summary="Video guidelines generated",
                            details={
                                "scenarios_count": len(artifact.get("content", {}).get("scenarios", [])),
                                "trigger_hypothesis_id": artifact.get("video_trigger_hypothesis_id")
                            },
                            related_ids={"cycle_id": cycle_id, "artifact_id": art_id}
                        ))
                else:
                    if artifact.get("status") != prev_art.get("status"):
                        events.append(TimelineEvent(
                            timestamp=ts,
                            turn=turn,
                            event_type=EventType.ARTIFACT_STATUS_CHANGED,
                            category="artifact",
                            summary=f"Artifact status: {prev_art.get('status')} -> {artifact.get('status')}",
                            details={
                                "type": artifact.get("type"),
                                "previous_status": prev_art.get("status"),
                                "new_status": artifact.get("status")
                            },
                            related_ids={"cycle_id": cycle_id, "artifact_id": art_id}
                        ))

                self._prev_artifacts[art_id] = artifact

        # Update prev cycles
        self._prev_cycles = current_cycles

        # === Detect Pattern Events ===
        understanding = child_data.get("understanding", {})
        patterns = understanding.get("patterns", [])
        current_patterns = {p.get("id"): p for p in patterns}

        for pattern_id, pattern in current_patterns.items():
            if pattern_id not in self._prev_patterns:
                events.append(TimelineEvent(
                    timestamp=ts,
                    turn=turn,
                    event_type=EventType.PATTERN_DETECTED,
                    category="pattern",
                    summary=f"Pattern detected: {pattern.get('theme')}",
                    details={
                        "theme": pattern.get("theme"),
                        "description": pattern.get("description"),
                        "confidence": pattern.get("confidence"),
                        "supporting_cycle_ids": pattern.get("supporting_cycle_ids", [])
                    },
                    related_ids={"pattern_id": pattern_id}
                ))

        self._prev_patterns = current_patterns

        # === Detect Insight Events ===
        insights = understanding.get("pending_insights", [])
        for insight in insights:
            if not insight.get("shared"):
                events.append(TimelineEvent(
                    timestamp=ts,
                    turn=turn,
                    event_type=EventType.INSIGHT_QUEUED,
                    category="insight",
                    summary=f"Insight queued: {insight.get('content', '')[:40]}...",
                    details={
                        "content": insight.get("content"),
                        "importance": insight.get("importance"),
                        "source": insight.get("source"),
                        "share_when": insight.get("share_when")
                    }
                ))

        return events

    def run_turn(self, turn_num: int, message: str, context: str) -> TurnSnapshot:
        """Run a single conversation turn and capture all events"""
        ts = datetime.now().isoformat()

        # Send message
        response_data = self.send_message(message)
        chitta_response = response_data.get("response", "")
        ui_data = response_data.get("ui_data", {})

        # Get full child data for detailed analysis
        child_data = self.get_child_data() or {}

        # Get child gestalt data (Living Gestalt fields)
        gestalt_data = self.get_child_gestalt() or {}

        # Detect all events
        events = self._detect_events(turn_num, child_data, ui_data)

        # Add conversation events
        events.insert(0, TimelineEvent(
            timestamp=ts,
            turn=turn_num,
            event_type=EventType.MESSAGE_SENT,
            category="conversation",
            summary=f"Parent: {message[:50]}...",
            details={"message": message, "context": context}
        ))
        events.insert(1, TimelineEvent(
            timestamp=ts,
            turn=turn_num,
            event_type=EventType.MESSAGE_RECEIVED,
            category="conversation",
            summary=f"Chitta: {chitta_response[:50]}...",
            details={"response": chitta_response}
        ))

        # Build turn snapshot
        stats = ui_data.get("stats", {})

        # Extract hypotheses summary from cycles
        hypotheses_summary = []
        for cycle in child_data.get("exploration_cycles", []):
            for h in cycle.get("hypotheses", []):
                hypotheses_summary.append({
                    "id": h.get("id"),
                    "theory": h.get("theory"),
                    "domain": h.get("domain"),
                    "status": h.get("status"),
                    "confidence": h.get("confidence"),
                    "evidence_count": len(h.get("evidence", []))
                })

        # Get session memory (from reflection service)
        session_memory_data = self.get_session_memory()
        memory_snapshot = {}
        if session_memory_data:
            memory_snapshot = {
                "memory": session_memory_data.get("memory", {}),
                "turn_count": session_memory_data.get("turn_count", 0),
                "last_reflection_turn": session_memory_data.get("last_reflection_turn", 0),
                "pending_reflection": session_memory_data.get("pending_reflection", False),
                "needs_reflection": session_memory_data.get("needs_reflection", False)
            }

        snapshot = TurnSnapshot(
            turn=turn_num,
            timestamp=ts,
            parent_message=message,
            chitta_response=chitta_response,
            events=events,
            child_profile={
                "name": child_data.get("developmental_data", {}).get("child_name"),
                "age": child_data.get("developmental_data", {}).get("age"),
                "gender": child_data.get("developmental_data", {}).get("gender"),
                "primary_concerns": child_data.get("developmental_data", {}).get("primary_concerns", [])
            },
            exploration_cycles=[
                {
                    "id": c.get("id"),
                    "status": c.get("status"),
                    "focus_domain": c.get("focus_domain"),
                    "hypotheses_count": len(c.get("hypotheses", [])),
                    "artifacts_count": len(c.get("artifacts", []))
                }
                for c in child_data.get("exploration_cycles", [])
            ],
            hypotheses_summary=hypotheses_summary,
            patterns=child_data.get("understanding", {}).get("patterns", []),
            artifacts=[
                {
                    "id": a.get("id"),
                    "type": a.get("type"),
                    "status": a.get("status")
                }
                for cycle in child_data.get("exploration_cycles", [])
                for a in cycle.get("artifacts", [])
            ],
            completeness=stats.get("completeness", 0),
            active_cycles_count=stats.get("active_cycles", 0),
            hypotheses_count=stats.get("hypotheses_count", 0),
            tool_calls=ui_data.get("tool_calls", []),
            conversation_memory=memory_snapshot,
            # === Living Gestalt Fields ===
            gestalt_identity=gestalt_data.get("identity", {}),
            gestalt_essence=gestalt_data.get("essence", {}),
            gestalt_strengths=gestalt_data.get("strengths", {}),
            gestalt_concerns=gestalt_data.get("concerns", {}),
            gestalt_history=gestalt_data.get("history", {}),
            gestalt_family=gestalt_data.get("family", {}),
            gestalt_understanding=gestalt_data.get("understanding", {}),
            gestalt_synthesis=gestalt_data.get("synthesis_reports", [])
        )

        # Add to report
        self.report.turns.append(snapshot)
        self.report.timeline.extend(events)
        self.report.total_events += len(events)

        # Update event counts
        for event in events:
            event_type = event.event_type
            if event_type not in self.report.events_by_type:
                self.report.events_by_type[event_type] = 0
            self.report.events_by_type[event_type] += 1

        return snapshot

    def run_turn_zero(self) -> Optional[TurnSnapshot]:
        """Run Turn 0: Initialize conversation and capture Chitta's greeting"""
        ts = datetime.now().isoformat()

        # Initialize conversation to get Chitta's greeting
        init_data = self.init_conversation()
        if not init_data:
            print("Warning: Failed to initialize conversation, skipping Turn 0")
            return None

        chitta_greeting = init_data.get("greeting", init_data.get("response", ""))
        ui_data = init_data.get("ui_data", {})

        # Get initial gestalt data
        gestalt_data = self.get_child_gestalt() or {}

        # Create Turn 0 event
        events = [
            TimelineEvent(
                timestamp=ts,
                turn=0,
                event_type=EventType.MESSAGE_RECEIVED,
                category="conversation",
                summary=f"Chitta (greeting): {chitta_greeting[:50]}...",
                details={"response": chitta_greeting, "is_greeting": True}
            )
        ]

        snapshot = TurnSnapshot(
            turn=0,
            timestamp=ts,
            parent_message="[Session Initialized]",
            chitta_response=chitta_greeting,
            events=events,
            child_profile={},
            exploration_cycles=[],
            hypotheses_summary=[],
            patterns=[],
            artifacts=[],
            completeness=0.0,
            active_cycles_count=0,
            hypotheses_count=0,
            tool_calls=ui_data.get("tool_calls", []),
            conversation_memory={},
            gestalt_identity=gestalt_data.get("identity", {}),
            gestalt_essence=gestalt_data.get("essence", {}),
            gestalt_strengths=gestalt_data.get("strengths", {}),
            gestalt_concerns=gestalt_data.get("concerns", {}),
            gestalt_history=gestalt_data.get("history", {}),
            gestalt_family=gestalt_data.get("family", {}),
            gestalt_understanding=gestalt_data.get("understanding", {}),
            gestalt_synthesis=gestalt_data.get("synthesis_reports", [])
        )

        # Add to report
        self.report.turns.append(snapshot)
        self.report.timeline.extend(events)
        self.report.total_events += len(events)

        return snapshot

    def run_scenario(self, scenario_name: str, messages: List[tuple]) -> XRayReport:
        """Run a complete scenario with multiple messages"""
        self.report.scenario_name = scenario_name

        print(f"\n{'='*80}")
        print(f"  CHITTA TEMPORAL DESIGN X-RAY TEST")
        print(f"{'='*80}")
        print(f"Session ID: {self.session_id}")
        print(f"Family ID: {self.family_id}")
        print(f"Scenario: {scenario_name}")
        print(f"{'='*80}\n")

        # === Turn 0: Chitta's greeting ===
        print(f"\n--- Turn 0: Chitta's Greeting ---")
        turn0_snapshot = self.run_turn_zero()
        if turn0_snapshot:
            print(f"Chitta: {turn0_snapshot.chitta_response[:200]}...")
            print(f"\n[Turn 0 captured - initial greeting]")
        time.sleep(0.5)

        for i, (context, message) in enumerate(messages, 1):
            print(f"\n--- Turn {i}: {context} ---")
            print(f"Parent: {message}")

            snapshot = self.run_turn(i, message, context)

            print(f"Chitta: {snapshot.chitta_response[:200]}...")
            print(f"\nEvents detected: {len(snapshot.events)}")
            for event in snapshot.events:
                if event.category != "conversation":
                    print(f"  - [{event.category}] {event.summary}")

            print(f"\nState: Completeness={snapshot.completeness:.1f}%, "
                  f"Cycles={snapshot.active_cycles_count}, "
                  f"Hypotheses={snapshot.hypotheses_count}")

            # Show gestalt evolution highlights
            if snapshot.gestalt_essence:
                qualities = snapshot.gestalt_essence.get("core_qualities", [])
                if qualities:
                    print(f"  Gestalt: core_qualities={qualities[:2]}...")

            # Wait longer for background reflection to process (runs every 3 turns for testing)
            # Reflection is async and may not complete in 0.5s
            if i % 3 == 0:
                time.sleep(3)  # Allow reflection to complete after every 3 turns
            else:
                time.sleep(1)  # Brief pause between other turns

        # Capture final state
        child_data = self.get_child_data() or {}
        self.report.final_child_profile = child_data.get("developmental_data", {})
        self.report.final_cycles = child_data.get("exploration_cycles", [])
        self.report.final_patterns = child_data.get("understanding", {}).get("patterns", [])

        # Fix counts from final state (diff-based counting can miss items)
        # Only update if we have valid final state data - don't overwrite event-based counts on error
        final_cycles = child_data.get("exploration_cycles", [])
        if final_cycles:
            # We have valid data from final state - use it
            self.report.cycles_created = len(final_cycles)

            total_hypotheses = 0
            completed_cycles = 0
            resolved_hypotheses = 0
            for cycle in final_cycles:
                hypotheses = cycle.get("hypotheses", [])
                total_hypotheses += len(hypotheses)
                if cycle.get("status") == "complete":
                    completed_cycles += 1
                for hyp in hypotheses:
                    if hyp.get("status") == "resolved":
                        resolved_hypotheses += 1

            self.report.hypotheses_formed = total_hypotheses
            self.report.cycles_completed = completed_cycles
            self.report.hypotheses_resolved = resolved_hypotheses
        # If final_cycles is empty, keep the event-based counts that were accumulated during the test

        return self.report

    def save_report(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Save the report in JSON and Markdown formats"""
        output_dir = output_dir or self.output_dir
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"xray_{self.report.scenario_name}_{timestamp}"

        # Save JSON (for UI dashboard)
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            # Convert dataclasses to dict
            report_dict = self._to_dict(self.report)
            json.dump(report_dict, f, ensure_ascii=False, indent=2)

        # Save Markdown (for human review)
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown())

        # Save HTML Dashboard (for interactive exploration)
        html_path = os.path.join(output_dir, f"{base_name}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_html_dashboard())

        print(f"\n{'='*80}")
        print(f"  REPORTS SAVED")
        print(f"{'='*80}")
        print(f"JSON (for dashboard): {json_path}")
        print(f"Markdown (for review): {md_path}")
        print(f"HTML (interactive):    {html_path}")

        return {"json": json_path, "markdown": md_path, "html": html_path}

    def _to_dict(self, obj) -> Any:
        """Recursively convert dataclasses to dicts"""
        if hasattr(obj, '__dataclass_fields__'):
            return {k: self._to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [self._to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, Enum):
            return obj.value
        return obj

    def _generate_markdown(self) -> str:
        """Generate a markdown report"""
        lines = [
            f"# Chitta Temporal Design X-Ray Report",
            f"",
            f"**Generated:** {self.report.generated_at}",
            f"**Session ID:** {self.report.session_id}",
            f"**Family ID:** {self.report.family_id}",
            f"**Scenario:** {self.report.scenario_name}",
            f"",
            f"---",
            f"",
            f"## Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Turns | {len(self.report.turns)} |",
            f"| Total Events | {self.report.total_events} |",
            f"| Cycles Created | {self.report.cycles_created} |",
            f"| Cycles Completed | {self.report.cycles_completed} |",
            f"| Hypotheses Formed | {self.report.hypotheses_formed} |",
            f"| Hypotheses Resolved | {self.report.hypotheses_resolved} |",
            f"| Artifacts Created | {self.report.artifacts_created} |",
            f"",
            f"### Events by Type",
            f"",
        ]

        for event_type, count in sorted(self.report.events_by_type.items()):
            lines.append(f"- **{event_type}**: {count}")

        # === Errors Section ===
        if self.errors:
            lines.extend([
                f"",
                f"### Errors Encountered",
                f"",
                f"| Turn | Context | Error | Details |",
                f"|------|---------|-------|---------|"
            ])
            for err in self.errors:
                turn = err.get("turn", "-")
                context = err.get("context", "unknown")
                error_msg = err.get("error", "")
                # Truncate long error messages
                if len(error_msg) > 60:
                    error_msg = error_msg[:57] + "..."
                details = err.get("details", {})
                details_str = ""
                if details:
                    # Show response_text or first key
                    if "response_text" in details and details["response_text"]:
                        details_str = details["response_text"][:40] + "..."
                    else:
                        # Show first non-empty detail
                        for k, v in details.items():
                            if v:
                                details_str = f"{k}: {str(v)[:30]}..."
                                break
                lines.append(f"| {turn} | {context} | {error_msg} | {details_str} |")
            lines.append(f"")

        # === NEW: Timeline Metrics Table (Feature 1) ===
        lines.extend(self._generate_timeline_metrics_table())

        # === NEW: Emergence Timeline (Feature 1 Enhanced) ===
        lines.extend(self._generate_emergence_timeline())

        lines.extend([
            f"",
            f"---",
            f"",
            f"## Timeline",
            f""
        ])

        # Group events by turn
        for turn in self.report.turns:
            lines.extend([
                f"### Turn {turn.turn}",
                f"",
                f"**Parent:** {turn.parent_message}",
                f"",
                f"**Chitta:** {turn.chitta_response}",
                f""
            ])

            # === Event Causation Chain (Feature 3) ===
            causation_lines = self._generate_event_causation_chain(turn)
            if causation_lines:
                lines.extend(causation_lines)
            else:
                # Fall back to flat event list if no meaningful chain
                lines.append(f"**Events:**")
                lines.append(f"")
                for event in turn.events:
                    if event.category != "conversation":
                        lines.append(f"- `[{event.category}]` {event.summary}")

            lines.extend([
                f"",
                f"**State Snapshot:**",
                f"- Completeness: {turn.completeness:.1f}%",
                f"- Active Cycles: {turn.active_cycles_count}",
                f"- Hypotheses: {turn.hypotheses_count}",
            ])

            # === NEW: Delta-Focused View (Feature 2) ===
            turn_idx = self.report.turns.index(turn)
            deltas = self._compute_turn_deltas(turn_idx)
            if deltas:
                lines.append(f"")
                lines.append(f"**Deltas (What Changed):**")
                for delta in deltas:
                    lines.append(f"- {delta}")

            # Add gestalt evolution if data exists
            if any([turn.gestalt_identity, turn.gestalt_essence, turn.gestalt_strengths,
                    turn.gestalt_concerns, turn.gestalt_history, turn.gestalt_family]):
                lines.append(f"")
                lines.append(f"**Gestalt Evolution:**")

                # Identity
                if turn.gestalt_identity:
                    identity = turn.gestalt_identity
                    name = identity.get("name") or identity.get("child_name")
                    age = identity.get("age") or identity.get("age_years")
                    gender = identity.get("gender")
                    if name or age or gender:
                        lines.append(f"- Identity: name={name}, age={age}, gender={gender}")

                # Essence
                if turn.gestalt_essence:
                    essence = turn.gestalt_essence
                    qualities = essence.get("core_qualities", [])
                    temperament = essence.get("temperament")
                    energy = essence.get("energy_pattern")
                    if qualities or temperament or energy:
                        parts = []
                        if temperament:
                            parts.append(f"temperament={temperament}")
                        if energy:
                            parts.append(f"energy={energy}")
                        if qualities:
                            parts.append(f"qualities={qualities[:3]}")
                        lines.append(f"- Essence: {', '.join(parts)}")

                # Strengths
                if turn.gestalt_strengths:
                    strengths = turn.gestalt_strengths
                    abilities = strengths.get("abilities", [])
                    interests = strengths.get("interests", [])
                    lights_up = strengths.get("what_lights_them_up", [])
                    if abilities or interests or lights_up:
                        parts = []
                        if abilities:
                            parts.append(f"abilities={abilities[:2]}")
                        if interests:
                            parts.append(f"interests={interests[:2]}")
                        if lights_up:
                            parts.append(f"lights_up={lights_up[:2]}")
                        lines.append(f"- Strengths: {', '.join(parts)}")

                # Concerns
                if turn.gestalt_concerns:
                    concerns = turn.gestalt_concerns
                    primary = concerns.get("primary_areas", [])
                    narrative = concerns.get("parent_narrative")
                    if primary or narrative:
                        parts = []
                        if primary:
                            parts.append(f"areas={primary}")
                        if narrative:
                            parts.append(f"narrative=\"{narrative[:50]}...\"" if len(str(narrative)) > 50 else f"narrative=\"{narrative}\"")
                        lines.append(f"- Concerns: {', '.join(parts)}")

                # Family
                if turn.gestalt_family:
                    family = turn.gestalt_family
                    structure = family.get("structure")
                    siblings = family.get("siblings", [])
                    languages = family.get("languages", [])
                    if structure or siblings or languages:
                        parts = []
                        if structure:
                            parts.append(f"structure={structure}")
                        if siblings:
                            parts.append(f"siblings={len(siblings)}")
                        if languages:
                            parts.append(f"languages={languages}")
                        lines.append(f"- Family: {', '.join(parts)}")

            # Add conversation memory info if available
            if turn.conversation_memory:
                memory = turn.conversation_memory.get("memory", {})
                last_reflection = turn.conversation_memory.get("last_reflection_turn", 0)
                needs_reflection = turn.conversation_memory.get("needs_reflection", False)

                # Check if memory has any content
                has_memory_content = any([
                    memory.get("parent_style"),
                    memory.get("topics_discussed"),
                    memory.get("emotional_patterns"),
                    memory.get("rapport_notes")
                ])

                if has_memory_content or last_reflection > 0:
                    lines.append(f"- Last Reflection: Turn {last_reflection}")
                    if needs_reflection:
                        lines.append(f"- ⏳ Reflection pending")

                    # Show memory content if present
                    if memory.get("parent_style"):
                        lines.append(f"- Parent Style: {memory.get('parent_style')}")
                    if memory.get("topics_discussed"):
                        topics = memory.get("topics_discussed", [])
                        if topics:
                            lines.append(f"- Topics Discussed: {', '.join(topics[:5])}")
                    if memory.get("rapport_notes"):
                        lines.append(f"- Rapport: {memory.get('rapport_notes')[:80]}...")

            lines.append(f"")

            if turn.hypotheses_summary:
                lines.append(f"**Hypotheses:**")
                lines.append(f"")
                for h in turn.hypotheses_summary:
                    lines.append(f"- `{h['id']}` [{h['status']}] {h['confidence']:.0%} - {h['domain']}: {h['theory'][:60]}...")
                lines.append(f"")

            lines.append(f"---")
            lines.append(f"")

        # === Gestalt Evolution Timeline (Feature 4) ===
        lines.extend(self._generate_gestalt_evolution())

        # === Hypothesis Lifecycles (Feature 3 from redesign) ===
        lines.extend(self._generate_hypothesis_lifecycles())

        # === Cross-Cycle Connection Map (Feature 4 from redesign) ===
        lines.extend(self._generate_cross_cycle_connections())

        # === Memory Evolution (Feature 5 from redesign) ===
        lines.extend(self._generate_memory_evolution())

        # Final state
        lines.extend([
            f"## Final State",
            f"",
            f"### Child Profile",
            f"",
        ])

        # Try to get profile from gestalt identity (new structure) first, then fall back to developmental_data
        profile = self.report.final_child_profile
        gestalt_identity = {}
        gestalt_concerns = {}
        if self.report.turns:
            last_turn = self.report.turns[-1]
            gestalt_identity = last_turn.gestalt_identity or {}
            gestalt_concerns = last_turn.gestalt_concerns or {}

        # Use gestalt identity if available, otherwise fall back to old structure
        name = gestalt_identity.get('name') or gestalt_identity.get('child_name') or profile.get('child_name', 'Unknown')
        age = gestalt_identity.get('age') or gestalt_identity.get('age_years') or profile.get('age', 'Unknown')
        gender = gestalt_identity.get('gender') or profile.get('gender', 'Unknown')
        concerns = gestalt_concerns.get('primary_areas', []) or profile.get('primary_concerns', [])

        lines.append(f"- **Name:** {name}")
        lines.append(f"- **Age:** {age}")
        lines.append(f"- **Gender:** {gender}")
        lines.append(f"- **Concerns:** {', '.join(concerns) if concerns else 'None captured'}")
        lines.append(f"")

        if self.report.final_cycles:
            lines.extend([
                f"### Final Exploration Cycles",
                f""
            ])

            for cycle in self.report.final_cycles:
                lines.extend([
                    f"#### Cycle `{cycle.get('id')}` - {cycle.get('focus_domain', 'Unknown')}",
                    f"",
                    f"- **Status:** {cycle.get('status')}",
                    f"- **Focus:** {cycle.get('focus_description', 'N/A')}",
                    f""
                ])

                for h in cycle.get("hypotheses", []):
                    status_emoji = "✅" if h.get("status") == "resolved" else "🔄" if h.get("status") == "active" else "💭"
                    lines.extend([
                        f"**{status_emoji} Hypothesis `{h.get('id')}`**",
                        f"",
                        f"| Field | Value |",
                        f"|-------|-------|",
                        f"| Theory | {h.get('theory')} |",
                        f"| Domain | {h.get('domain')} |",
                        f"| Status | {h.get('status')} |",
                        f"| Confidence | {h.get('confidence', 0):.0%} |",
                        f"| Evidence Count | {len(h.get('evidence', []))} |",
                        f""
                    ])

                    if h.get("evidence"):
                        lines.append(f"**Evidence:**")
                        for e in h.get("evidence", []):
                            lines.append(f"- [{e.get('source')}] {e.get('content')}")
                        lines.append(f"")

        if self.report.final_patterns:
            lines.extend([
                f"### Patterns Detected",
                f""
            ])
            for p in self.report.final_patterns:
                lines.append(f"- **{p.get('theme')}** ({p.get('confidence', 0):.0%}): {p.get('description')}")
            lines.append(f"")

        # === Living Gestalt Section (Final State) ===
        # Get the last turn's gestalt data for comprehensive final state view
        if self.report.turns:
            last_turn = self.report.turns[-1]
            has_gestalt = any([
                last_turn.gestalt_identity, last_turn.gestalt_essence,
                last_turn.gestalt_strengths, last_turn.gestalt_concerns,
                last_turn.gestalt_history, last_turn.gestalt_family
            ])

            if has_gestalt:
                lines.extend([
                    f"### Living Gestalt (Complete Picture)",
                    f"",
                    f"*Full child understanding accumulated throughout the conversation*",
                    f""
                ])

                # Identity
                if last_turn.gestalt_identity:
                    identity = last_turn.gestalt_identity
                    lines.append(f"#### Identity")
                    name = identity.get("name") or identity.get("child_name")
                    age = identity.get("age") or identity.get("age_years")
                    birth_date = identity.get("birth_date")
                    gender = identity.get("gender")
                    if name:
                        lines.append(f"- **Name:** {name}")
                    if age:
                        lines.append(f"- **Age:** {age}")
                    if birth_date:
                        lines.append(f"- **Birth Date:** {birth_date}")
                    if gender:
                        lines.append(f"- **Gender:** {gender}")
                    lines.append(f"")

                # Essence
                if last_turn.gestalt_essence:
                    essence = last_turn.gestalt_essence
                    lines.append(f"#### Essence (Who They Are)")
                    temperament = essence.get("temperament")
                    energy = essence.get("energy_pattern")
                    qualities = essence.get("core_qualities", [])
                    communication = essence.get("communication_style")
                    if temperament:
                        lines.append(f"- **Temperament:** {temperament}")
                    if energy:
                        lines.append(f"- **Energy Pattern:** {energy}")
                    if qualities:
                        lines.append(f"- **Core Qualities:** {', '.join(qualities)}")
                    if communication:
                        lines.append(f"- **Communication Style:** {communication}")
                    lines.append(f"")

                # Strengths
                if last_turn.gestalt_strengths:
                    strengths = last_turn.gestalt_strengths
                    lines.append(f"#### Strengths & Interests")
                    abilities = strengths.get("abilities", [])
                    interests = strengths.get("interests", [])
                    lights_up = strengths.get("what_lights_them_up", [])
                    learning = strengths.get("learning_style")
                    if abilities:
                        lines.append(f"- **Abilities:** {', '.join(abilities)}")
                    if interests:
                        lines.append(f"- **Interests:** {', '.join(interests)}")
                    if lights_up:
                        lines.append(f"- **What Lights Them Up:** {', '.join(lights_up)}")
                    if learning:
                        lines.append(f"- **Learning Style:** {learning}")
                    lines.append(f"")

                # Concerns
                if last_turn.gestalt_concerns:
                    concerns = last_turn.gestalt_concerns
                    lines.append(f"#### Concerns (Parent Perspective)")
                    primary = concerns.get("primary_areas", [])
                    details = concerns.get("details")
                    narrative = concerns.get("parent_narrative")
                    triggers = concerns.get("known_triggers", [])
                    if primary:
                        lines.append(f"- **Primary Areas:** {', '.join(primary)}")
                    if details:
                        lines.append(f"- **Details:** {details}")
                    if narrative:
                        lines.append(f"- **Parent's Words:** \"{narrative}\"")
                    if triggers:
                        lines.append(f"- **Known Triggers:** {', '.join(triggers)}")
                    lines.append(f"")

                # History
                if last_turn.gestalt_history:
                    history = last_turn.gestalt_history
                    lines.append(f"#### Developmental History")
                    birth = history.get("birth")
                    early_dev = history.get("early_development")
                    milestones = history.get("milestones", [])
                    if birth:
                        lines.append(f"- **Birth:** {birth}")
                    if early_dev:
                        lines.append(f"- **Early Development:** {early_dev}")
                    if milestones:
                        lines.append(f"- **Milestones:**")
                        for m in milestones[:5]:  # Limit to 5
                            if isinstance(m, dict):
                                lines.append(f"  - {m.get('milestone', '')} @ {m.get('age', '?')}")
                            else:
                                lines.append(f"  - {m}")
                    lines.append(f"")

                # Family
                if last_turn.gestalt_family:
                    family = last_turn.gestalt_family
                    lines.append(f"#### Family Context")
                    structure = family.get("structure")
                    siblings = family.get("siblings", [])
                    languages = family.get("languages", [])
                    parenting = family.get("parenting_approach")
                    routines = family.get("daily_routines")
                    if structure:
                        lines.append(f"- **Family Structure:** {structure}")
                    if siblings:
                        lines.append(f"- **Siblings:** {len(siblings)} ({', '.join(siblings[:3])})")
                    if languages:
                        lines.append(f"- **Languages:** {', '.join(languages)}")
                    if parenting:
                        lines.append(f"- **Parenting Approach:** {parenting}")
                    if routines:
                        lines.append(f"- **Daily Routines:** {routines}")
                    lines.append(f"")

        # === Tool Call Flow Summary ===
        # Aggregate tool calls across all turns for flow visualization
        all_tool_calls = []
        for turn in self.report.turns:
            for tc in turn.tool_calls:
                all_tool_calls.append({
                    "turn": turn.turn,
                    "tool": tc.get("tool"),
                    "args_summary": self._summarize_args(tc.get("arguments", {})),
                    "result_summary": self._summarize_result(tc.get("result", {}))
                })

        if all_tool_calls:
            lines.extend([
                f"### Tool Call Flow",
                f"",
                f"*Sequence of internal tool calls showing data extraction and hypothesis formation*",
                f""
            ])

            for tc in all_tool_calls:
                result_str = f" → {tc['result_summary']}" if tc['result_summary'] else ""
                lines.append(f"- **Turn {tc['turn']}:** `{tc['tool']}` {tc['args_summary']}{result_str}")

            lines.append(f"")

        # Add final conversation memory section
        if self.report.turns:
            last_turn = self.report.turns[-1]
            if last_turn.conversation_memory:
                memory = last_turn.conversation_memory.get("memory", {})
                last_reflection = last_turn.conversation_memory.get("last_reflection_turn", 0)

                # Check if memory has any content
                has_memory_content = any([
                    memory.get("parent_style"),
                    memory.get("topics_discussed"),
                    memory.get("emotional_patterns"),
                    memory.get("rapport_notes")
                ])

                if has_memory_content or last_reflection > 0:
                    lines.extend([
                        f"### Conversation Memory (Reflection)",
                        f"",
                        f"*Distilled relationship knowledge from the \"slow brain\" reflection system*",
                        f"",
                        f"- **Last Reflection:** Turn {last_reflection}",
                    ])

                    if memory.get("parent_style"):
                        lines.append(f"- **Parent Communication Style:** {memory.get('parent_style')}")
                    if memory.get("emotional_patterns"):
                        lines.append(f"- **Emotional Patterns:** {memory.get('emotional_patterns')}")
                    if memory.get("topics_discussed"):
                        topics = memory.get("topics_discussed", [])
                        if topics:
                            lines.append(f"- **Topics Discussed:** {', '.join(topics)}")
                    if memory.get("rapport_notes"):
                        lines.append(f"- **Rapport Notes:** {memory.get('rapport_notes')}")
                    if memory.get("vocabulary_preferences"):
                        lines.append(f"- **Vocabulary Preferences:** {memory.get('vocabulary_preferences')}")

                    lines.append(f"")

        lines.extend([
            f"---",
            f"",
            f"*End of X-Ray Report*"
        ])

        return "\n".join(lines)

    def _generate_timeline_metrics_table(self) -> List[str]:
        """Generate a metrics table showing state evolution across turns (Feature 1)"""
        lines = [
            f"",
            f"## Timeline Metrics",
            f"",
            f"*At-a-glance view of state evolution across turns*",
            f"",
            f"| Turn | Completeness | Cycles | Hypotheses | Key Events |",
            f"|------|-------------|--------|------------|------------|"
        ]

        for turn in self.report.turns:
            # Count non-conversation events for "Key Events" column
            key_events = []
            tool_count = 0

            for event in turn.events:
                if event.category == "tool":
                    tool_count += 1
                elif event.category == "cycle":
                    if "created" in event.event_type.lower():
                        key_events.append("cycle+")
                    elif "completed" in event.event_type.lower():
                        key_events.append("cycle✓")
                elif event.category == "hypothesis":
                    if "formed" in event.event_type.lower():
                        key_events.append("hyp+")
                    elif "resolved" in event.event_type.lower():
                        key_events.append("hyp✓")
                    elif "confidence" in event.event_type.lower() or "evidence" in event.event_type.lower():
                        key_events.append("hyp↑")
                elif event.category == "pattern":
                    key_events.append("pattern")
                elif event.category == "artifact":
                    key_events.append("artifact")

            # Add tool count if any
            if tool_count > 0:
                key_events.insert(0, f"tool({tool_count})")

            # Format key events
            events_str = ", ".join(key_events) if key_events else "-"
            if len(events_str) > 35:
                events_str = events_str[:32] + "..."

            lines.append(
                f"| {turn.turn} | {turn.completeness:.1f}% | {turn.active_cycles_count} | {turn.hypotheses_count} | {events_str} |"
            )

        lines.append(f"")
        return lines

    def _generate_emergence_timeline(self) -> List[str]:
        """Generate Emergence Timeline - the narrative of understanding (Feature 1 Enhanced)

        Shows the story of emergence: Chitta leads with questions, parent responds,
        understanding crystallizes. This is the "bird's eye view" of how Chitta went
        from knowing nothing to understanding this child.

        Key insight: Chitta speaks FIRST in each turn (asks questions), then parent responds.
        The previous turn's Chitta question sets up what the parent will reveal.
        """
        lines = [
            f"",
            f"## Emergence Timeline",
            f"",
            f"*The story of how understanding emerged - Chitta leads, parent responds*",
            f"",
            f"| Turn | Chitta Asked | Parent Revealed | What We Learned | Impact |",
            f"|------|--------------|-----------------|-----------------|--------|"
        ]

        if not self.report.turns:
            lines.append("| - | - | - | - | - |")
            lines.append(f"")
            return lines

        prev_chitta_question = "(First contact)"  # Turn 0 has no previous question

        for i, turn in enumerate(self.report.turns):
            turn_num = turn.turn

            # Extract what Chitta asked in the PREVIOUS turn (sets up this response)
            if i > 0:
                prev_turn = self.report.turns[i - 1]
                prev_chitta_question = self._extract_chitta_question(prev_turn.chitta_response)
            else:
                prev_chitta_question = "(Opening)"

            # Extract what parent revealed (truncated)
            parent_trigger = self._extract_parent_trigger(turn.parent_message)

            # Analyze what NEW understanding emerged this turn
            discoveries = self._analyze_turn_discoveries(turn, i)

            # Classify the impact on overall understanding
            impact = self._classify_turn_impact(turn, i)

            lines.append(
                f"| {turn_num} | {prev_chitta_question} | {parent_trigger} | {discoveries} | {impact} |"
            )

        lines.append(f"")

        # Add narrative summary
        lines.extend(self._generate_emergence_narrative())

        return lines

    def _extract_chitta_question(self, chitta_response: str) -> str:
        """Extract the main question Chitta asked from the response.

        Chitta's responses typically end with a question that guides the parent.
        This extracts that guiding question for the timeline.
        """
        if not chitta_response:
            return "—"

        # Find the last question mark and extract that sentence
        response = chitta_response.strip()

        # Look for questions (ending with ?)
        sentences = response.replace('?', '?\n').split('\n')
        questions = [s.strip() for s in sentences if s.strip().endswith('?')]

        if questions:
            # Take the last question (the one that guides parent's next response)
            question = questions[-1]
            # Truncate for display
            if len(question) > 35:
                return question[:32] + "..."
            return question

        # No question found - summarize what Chitta said
        if len(response) > 35:
            return response[:32] + "..."
        return response

    def _extract_parent_trigger(self, parent_message: str) -> str:
        """Extract the key phrase from parent's message that triggered understanding."""
        if not parent_message:
            return "—"

        msg = parent_message.strip()

        # Truncate for table display
        if len(msg) > 35:
            return f'"{msg[:32]}..."'
        return f'"{msg}"'

    def _analyze_turn_discoveries(self, turn: 'TurnSnapshot', turn_idx: int) -> str:
        """Analyze what NEW understanding emerged this turn.

        Returns a concise description of discoveries:
        - Identity revealed (name, age)
        - Concern identified
        - Hypothesis formed
        - Pattern detected
        - Contradiction found
        - Evidence added
        """
        discoveries = []

        # Check events for what happened
        for event in turn.events:
            if event.category == "cycle":
                if "created" in event.event_type.lower():
                    domain = event.details.get("domain", "")
                    discoveries.append(f"New cycle: {domain}")

            elif event.category == "hypothesis":
                if "formed" in event.event_type.lower():
                    domain = event.details.get("domain", "")
                    discoveries.append(f"Hypothesis: {domain}")
                elif "evidence" in event.event_type.lower():
                    discoveries.append("Evidence+")
                elif "confidence" in event.event_type.lower():
                    old = event.details.get("old_confidence", 0)
                    new = event.details.get("new_confidence", 0)
                    if isinstance(old, (int, float)) and isinstance(new, (int, float)):
                        if new > old:
                            discoveries.append("Confidence↑")
                        elif new < old:
                            discoveries.append("Confidence↓")

            elif event.category == "pattern":
                theme = event.details.get("theme", "pattern")
                if len(theme) > 15:
                    theme = theme[:12] + "..."
                discoveries.append(f"Pattern: {theme}")

            elif event.category == "tool":
                tool_name = event.details.get("tool", "")
                args = event.details.get("arguments", {})

                # Check for identity discovery
                if "update_child" in tool_name:
                    if args.get("child_name"):
                        discoveries.append(f"Name: {args['child_name']}")
                    if args.get("age"):
                        discoveries.append(f"Age: {args['age']}")
                    if args.get("gender") and args.get("gender") != "unknown":
                        discoveries.append(f"Gender: {args['gender']}")
                    concerns = args.get("primary_concerns", [])
                    if concerns:
                        discoveries.append(f"Concerns: {len(concerns)}")

                # Check for story capture
                elif "capture_story" in tool_name:
                    story_type = args.get("story_type", args.get("type", ""))
                    if story_type:
                        discoveries.append(f"Story: {story_type}")

        # Compare to previous turn for deltas
        if turn_idx > 0 and turn_idx < len(self.report.turns):
            prev = self.report.turns[turn_idx - 1]

            # Check for new cycles
            if turn.active_cycles_count > prev.active_cycles_count:
                delta = turn.active_cycles_count - prev.active_cycles_count
                if f"New cycle" not in str(discoveries):
                    discoveries.append(f"+{delta} cycle(s)")

            # Check for new hypotheses
            if turn.hypotheses_count > prev.hypotheses_count:
                delta = turn.hypotheses_count - prev.hypotheses_count
                if "Hypothesis" not in str(discoveries):
                    discoveries.append(f"+{delta} hyp")

        # Return formatted discoveries
        if not discoveries:
            return "—"

        result = ", ".join(discoveries[:3])  # Limit to 3 items
        if len(discoveries) > 3:
            result += f" +{len(discoveries)-3}"

        if len(result) > 40:
            return result[:37] + "..."
        return result

    def _classify_turn_impact(self, turn: 'TurnSnapshot', turn_idx: int) -> str:
        """Classify the impact of this turn on overall understanding.

        Categories:
        - GREETING: Opening exchange
        - IDENTITY: Child identified
        - CONCERN: Concern area opened
        - PATTERN: Cross-concern pattern found
        - CONTRADICTION: Evidence contradicts hypothesis
        - DEEPENING: Understanding refined
        - NEW_DOMAIN: New domain/cycle opened
        """
        impact_markers = []

        # Check events for impact classification
        has_identity = False
        has_concern = False
        has_cycle = False
        has_hypothesis = False
        has_pattern = False
        has_evidence = False

        for event in turn.events:
            if event.category == "tool":
                tool_name = event.details.get("tool", "")
                args = event.details.get("arguments", {})

                if "update_child" in tool_name:
                    if args.get("child_name") or args.get("age"):
                        has_identity = True
                    if args.get("primary_concerns"):
                        has_concern = True

            elif event.category == "cycle" and "created" in event.event_type.lower():
                has_cycle = True

            elif event.category == "hypothesis":
                if "formed" in event.event_type.lower():
                    has_hypothesis = True
                elif "evidence" in event.event_type.lower():
                    has_evidence = True

            elif event.category == "pattern":
                has_pattern = True

        # Determine primary impact
        if turn_idx == 0:
            return "🌱 First contact"

        if has_identity and turn_idx <= 3:
            return "👶 Child identified"

        if has_cycle:
            return "🔍 New exploration"

        if has_pattern:
            return "🔗 Pattern forming"

        if has_hypothesis:
            return "💡 Hypothesis formed"

        if has_evidence:
            return "📎 Evidence added"

        if has_concern:
            return "⚠️ Concern noted"

        # Check for completeness jump
        if turn_idx > 0:
            prev = self.report.turns[turn_idx - 1]
            completeness_delta = turn.completeness - prev.completeness
            if completeness_delta >= 0.1:
                return "📈 Understanding+"

        return "💬 Continuing"

    def _generate_emergence_narrative(self) -> List[str]:
        """Generate a narrative summary of the emergence story."""
        lines = [
            f"",
            f"### Emergence Story",
            f""
        ]

        if not self.report.turns:
            lines.append("*No conversation recorded*")
            return lines

        # Build narrative from turns
        narrative_parts = []

        # Find key milestones
        identity_turn = None
        first_concern_turn = None
        first_hypothesis_turn = None
        first_pattern_turn = None

        for i, turn in enumerate(self.report.turns):
            for event in turn.events:
                if event.category == "tool":
                    tool_name = event.details.get("tool", "")
                    args = event.details.get("arguments", {})
                    if "update_child" in tool_name:
                        if args.get("child_name") and identity_turn is None:
                            identity_turn = turn.turn
                        if args.get("primary_concerns") and first_concern_turn is None:
                            first_concern_turn = turn.turn

                elif event.category == "hypothesis" and "formed" in event.event_type.lower():
                    if first_hypothesis_turn is None:
                        first_hypothesis_turn = turn.turn

                elif event.category == "pattern":
                    if first_pattern_turn is None:
                        first_pattern_turn = turn.turn

        # Build narrative
        if identity_turn:
            narrative_parts.append(f"**Turn {identity_turn}**: Child's identity emerged")

        if first_concern_turn:
            narrative_parts.append(f"**Turn {first_concern_turn}**: First concern area identified")

        if first_hypothesis_turn:
            narrative_parts.append(f"**Turn {first_hypothesis_turn}**: First hypothesis formed")

        if first_pattern_turn:
            narrative_parts.append(f"**Turn {first_pattern_turn}**: Cross-concern pattern detected")

        if narrative_parts:
            lines.append("**Key Milestones:**")
            lines.append("")
            for part in narrative_parts:
                lines.append(f"- {part}")
            lines.append("")
        else:
            lines.append("*Conversation still in early exploration phase*")
            lines.append("")

        # Final understanding state
        if self.report.turns:
            final = self.report.turns[-1]
            lines.append(f"**Current State:** {final.completeness:.1f}% complete, "
                        f"{final.active_cycles_count} active cycles, "
                        f"{final.hypotheses_count} hypotheses")
            lines.append("")

        return lines

    def _generate_event_causation_chain(self, turn: 'TurnSnapshot') -> List[str]:
        """Generate visual causation flow boxes for a turn (Feature 2 Enhanced)

        Shows the complete cause-effect chain with visual flow boxes:

        ┌─────────────────────────────────────────────┐
        │ PARENT INPUT (response to Chitta's Q)       │
        └───────────────────┬─────────────────────────┘
                            ▼
        ┌─────────────────────────────────────────────┐
        │ EXTRACTION / STORY CAPTURE                   │
        └───────────────────┬─────────────────────────┘
                            ▼
        ┌─────────────────────────────────────────────┐
        │ HYPOTHESIS / PATTERN DETECTION               │
        └─────────────────────────────────────────────┘

        Key insight: Chitta leads (asks questions), parent responds, then processing happens.
        """
        lines = []

        # Categorize tool calls by their function in the flow
        extraction_tools = []  # update_child_understanding
        story_tools = []       # capture_story
        pattern_tools = []     # note_pattern
        hypothesis_tools = []  # form_hypothesis
        evidence_tools = []    # update_hypothesis_evidence
        other_tools = []       # other tools

        # Categorize events
        outcome_events = []
        state_change_events = []

        for event in turn.events:
            if event.category == "tool":
                tool_name = event.details.get("tool", event.summary.replace("Tool called: ", ""))
                if "update_child" in tool_name:
                    extraction_tools.append(event)
                elif "capture_story" in tool_name:
                    story_tools.append(event)
                elif "note_pattern" in tool_name:
                    pattern_tools.append(event)
                elif "form_hypothesis" in tool_name:
                    hypothesis_tools.append(event)
                elif "evidence" in tool_name or "update_hypothesis" in tool_name:
                    evidence_tools.append(event)
                else:
                    other_tools.append(event)
            elif event.category in ["cycle", "hypothesis"]:
                if any(x in event.event_type.lower() for x in ["created", "formed"]):
                    outcome_events.append(event)
                elif any(x in event.event_type.lower() for x in ["confidence", "evidence", "updated"]):
                    state_change_events.append(event)
            elif event.category == "pattern":
                outcome_events.append(event)
            elif event.category == "artifact":
                outcome_events.append(event)

        # Only show chain if there's meaningful activity
        all_tools = extraction_tools + story_tools + pattern_tools + hypothesis_tools + evidence_tools + other_tools
        if not all_tools and not outcome_events:
            return lines

        lines.append(f"**Causation Flow:**")
        lines.append(f"")
        lines.append(f"```")

        # 1. Parent Input Box (responding to Chitta's question from previous turn)
        parent_msg = turn.parent_message
        if len(parent_msg) > 45:
            parent_msg = parent_msg[:42] + "..."

        lines.append(f"┌{'─' * 50}┐")
        lines.append(f"│ PARENT INPUT                                     │")
        lines.append(f"│ \"{parent_msg}\"{'':>{48 - len(parent_msg)}}│")
        lines.append(f"└{'─' * 24}┬{'─' * 25}┘")
        lines.append(f"                         ▼")

        # 2. Extraction Stage (if any)
        if extraction_tools:
            lines.append(f"┌{'─' * 50}┐")
            lines.append(f"│ EXTRACTION (update_child_understanding)         │")
            for event in extraction_tools[:2]:  # Max 2 to fit
                args = event.details.get("arguments", {})
                # Show key extracted info
                extracted = []
                if args.get("child_name"):
                    extracted.append(f"name={args['child_name']}")
                if args.get("age"):
                    extracted.append(f"age={args['age']}")
                if args.get("primary_concerns"):
                    concerns = args['primary_concerns'][:2]  # Max 2
                    extracted.append(f"concerns={concerns}")
                if extracted:
                    summary = ", ".join(extracted)
                    if len(summary) > 46:
                        summary = summary[:43] + "..."
                    lines.append(f"│ • {summary:46}│")
            lines.append(f"└{'─' * 24}┬{'─' * 25}┘")
            lines.append(f"                         ▼")

        # 3. Story Capture Stage (if any)
        if story_tools:
            lines.append(f"┌{'─' * 50}┐")
            lines.append(f"│ STORY CAPTURED (capture_story)                  │")
            for event in story_tools[:2]:
                args = event.details.get("arguments", {})
                story_type = args.get("story_type", args.get("type", ""))
                context = args.get("context", "")
                if story_type or context:
                    summary = f"type={story_type}" if story_type else ""
                    if context:
                        summary += f", ctx={context[:20]}" if summary else f"ctx={context[:30]}"
                    if len(summary) > 46:
                        summary = summary[:43] + "..."
                    lines.append(f"│ • {summary:46}│")
            lines.append(f"└{'─' * 24}┬{'─' * 25}┘")
            lines.append(f"                         ▼")

        # 4. Pattern Detection Stage (if any)
        if pattern_tools:
            lines.append(f"┌{'─' * 50}┐")
            lines.append(f"│ PATTERN DETECTED (note_pattern)                 │")
            for event in pattern_tools[:2]:
                args = event.details.get("arguments", {})
                theme = args.get("theme", args.get("pattern", ""))
                if len(theme) > 46:
                    theme = theme[:43] + "..."
                if theme:
                    lines.append(f"│ • \"{theme}\"{'':>{44 - len(theme)}}│")
            lines.append(f"└{'─' * 24}┬{'─' * 25}┘")
            lines.append(f"                         ▼")

        # 5. Hypothesis Formation Stage (if any)
        if hypothesis_tools:
            lines.append(f"┌{'─' * 50}┐")
            lines.append(f"│ HYPOTHESIS FORMED (form_hypothesis)             │")
            for event in hypothesis_tools[:2]:
                args = event.details.get("arguments", {})
                theory = args.get("theory", "")
                confidence = args.get("confidence", 0)
                if len(theory) > 35:
                    theory = theory[:32] + "..."
                if theory:
                    conf_str = f"{confidence:.0%}" if isinstance(confidence, (int, float)) and confidence <= 1 else str(confidence)
                    lines.append(f"│ • \"{theory}\" ({conf_str}){'':>{35 - len(theory)}}│")
            lines.append(f"└{'─' * 24}┬{'─' * 25}┘")
            lines.append(f"                         ▼")

        # 6. Evidence Updates (if any)
        if evidence_tools:
            lines.append(f"┌{'─' * 50}┐")
            lines.append(f"│ EVIDENCE ADDED (update_hypothesis_evidence)     │")
            for event in evidence_tools[:2]:
                args = event.details.get("arguments", {})
                content = args.get("content", args.get("evidence", ""))
                effect = args.get("effect", "supports")
                if len(content) > 35:
                    content = content[:32] + "..."
                if content:
                    lines.append(f"│ • [{effect}] \"{content}\"{'':>{32 - len(content)}}│")
            lines.append(f"└{'─' * 24}┬{'─' * 25}┘")
            lines.append(f"                         ▼")

        # 7. State Delta Summary
        lines.append(f"┌{'─' * 50}┐")
        lines.append(f"│ STATE DELTA                                      │")
        lines.append(f"│ • Completeness: {turn.completeness:.1f}%{'':>32}│")
        lines.append(f"│ • Active Cycles: {turn.active_cycles_count}{'':>31}│")
        lines.append(f"│ • Hypotheses: {turn.hypotheses_count}{'':>34}│")
        lines.append(f"└{'─' * 50}┘")

        lines.append(f"```")
        lines.append(f"")
        return lines

    def _compute_turn_deltas(self, turn_idx: int) -> List[str]:
        """Compute what CHANGED in this turn compared to previous (Feature 2)"""
        if turn_idx < 0 or turn_idx >= len(self.report.turns):
            return []

        current = self.report.turns[turn_idx]
        prev = self.report.turns[turn_idx - 1] if turn_idx > 0 else None

        deltas = []

        # Completeness delta
        prev_completeness = prev.completeness if prev else 0.0
        if current.completeness != prev_completeness:
            delta_val = current.completeness - prev_completeness
            delta_sign = "+" if delta_val > 0 else ""
            deltas.append(f"Completeness: {prev_completeness:.1f}% -> {current.completeness:.1f}% ({delta_sign}{delta_val:.1f}%)")

        # Cycles delta
        prev_cycles = prev.active_cycles_count if prev else 0
        if current.active_cycles_count != prev_cycles:
            delta_val = current.active_cycles_count - prev_cycles
            if delta_val > 0:
                deltas.append(f"NEW Cycles: +{delta_val} (now {current.active_cycles_count})")
            else:
                deltas.append(f"Cycles completed: {abs(delta_val)} (now {current.active_cycles_count})")

        # Hypotheses delta
        prev_hyp = prev.hypotheses_count if prev else 0
        if current.hypotheses_count != prev_hyp:
            delta_val = current.hypotheses_count - prev_hyp
            if delta_val > 0:
                deltas.append(f"NEW Hypotheses: +{delta_val} (now {current.hypotheses_count})")
            else:
                deltas.append(f"Hypotheses resolved: {abs(delta_val)} (now {current.hypotheses_count})")

        # Detect specific events that happened this turn
        for event in current.events:
            if event.category == "cycle" and "created" in event.event_type.lower():
                cycle_id = event.related_ids.get("cycle_id", "?")[:8]
                domain = event.details.get("domain", "?")
                deltas.append(f"+ Cycle `{cycle_id}` ({domain})")

            elif event.category == "hypothesis" and "formed" in event.event_type.lower():
                hyp_id = event.related_ids.get("hypothesis_id", "?")[:8]
                theory = event.details.get("theory", "")
                if len(theory) > 50:
                    theory = theory[:47] + "..."
                confidence = event.details.get("confidence", 0)
                if isinstance(confidence, (int, float)):
                    conf_str = f"{confidence:.0%}" if confidence <= 1 else f"{confidence}%"
                else:
                    conf_str = str(confidence)
                deltas.append(f"+ Hypothesis `{hyp_id}`: \"{theory}\" ({conf_str})")

            elif event.category == "hypothesis" and "evidence" in event.event_type.lower():
                hyp_id = event.related_ids.get("hypothesis_id", "?")[:8]
                content = event.details.get("content", "")
                if len(content) > 40:
                    content = content[:37] + "..."
                deltas.append(f"+ Evidence -> `{hyp_id}`: \"{content}\"")

            elif event.category == "hypothesis" and "confidence" in event.event_type.lower():
                hyp_id = event.related_ids.get("hypothesis_id", "?")[:8]
                new_conf = event.details.get("new_confidence", "?")
                old_conf = event.details.get("old_confidence", "?")
                deltas.append(f"~ Confidence `{hyp_id}`: {old_conf} -> {new_conf}")

            elif event.category == "pattern":
                theme = event.details.get("theme", event.summary)
                if len(theme) > 50:
                    theme = theme[:47] + "..."
                deltas.append(f"+ Pattern detected: \"{theme}\"")

            elif event.category == "artifact":
                artifact_type = event.details.get("type", "unknown")
                deltas.append(f"+ Artifact created: {artifact_type}")

        return deltas

    def _summarize_args(self, args: Dict[str, Any]) -> str:
        """Summarize tool call arguments for concise display"""
        if not args:
            return ""

        parts = []

        # Child understanding fields
        if "child_name" in args:
            parts.append(f"name={args['child_name']}")
        if "age" in args:
            parts.append(f"age={args['age']}")
        if "gender" in args:
            parts.append(f"gender={args['gender']}")
        if "primary_concerns" in args:
            concerns = args["primary_concerns"]
            if concerns:
                parts.append(f"concerns={concerns[:2]}...")

        # Hypothesis formation
        if "theory" in args:
            theory = args["theory"]
            if len(theory) > 40:
                theory = theory[:37] + "..."
            parts.append(f"theory=\"{theory}\"")
        if "domain" in args:
            parts.append(f"domain={args['domain']}")

        # Evidence
        if "content" in args and "hypothesis_id" in args:
            content = args["content"]
            if len(content) > 30:
                content = content[:27] + "..."
            parts.append(f"evidence=\"{content}\"")

        # Pattern/Story
        if "pattern_type" in args:
            parts.append(f"pattern={args['pattern_type']}")
        if "story_type" in args:
            parts.append(f"story={args['story_type']}")

        if not parts:
            # Fallback: show first 2 keys
            for key in list(args.keys())[:2]:
                val = args[key]
                if isinstance(val, str) and len(val) > 20:
                    val = val[:17] + "..."
                parts.append(f"{key}={val}")

        return f"({', '.join(parts)})" if parts else ""

    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Summarize tool call result for concise display"""
        if not result:
            return ""

        parts = []

        # Common result fields
        if "fields_updated" in result:
            fields = result["fields_updated"]
            if fields:
                parts.append(f"updated: {fields}")
        if "new_completeness" in result:
            completeness = result["new_completeness"]
            if completeness is not None:
                parts.append(f"completeness={completeness:.1%}")
        if "hypothesis_id" in result:
            parts.append(f"hyp={result['hypothesis_id']}")
        if "cycle_id" in result:
            parts.append(f"cycle={result['cycle_id']}")
        if "success" in result:
            parts.append("✓" if result["success"] else "✗")
        if "status" in result:
            parts.append(f"status={result['status']}")

        return ", ".join(parts) if parts else ""

    def _generate_gestalt_evolution(self) -> List[str]:
        """Generate Gestalt Evolution section (Feature 4)

        Shows how understanding of the child deepens across turns -
        a narrative of discovery tracking when gestalt fields first appear or change.
        """
        lines = []
        lines.append(f"## Gestalt Evolution")
        lines.append(f"")

        if not self.report.turns:
            lines.append("*No turns recorded*")
            lines.append(f"")
            return lines

        # Track evolution of gestalt fields across turns
        evolution_events = []

        # Previous state for comparison
        prev_identity = {}
        prev_concerns = []
        prev_strengths = []
        prev_essence = {}
        prev_family = {}
        prev_history = {}

        for turn in self.report.turns:
            turn_events = []

            # Track Identity changes
            curr_identity = turn.gestalt_identity or {}
            if curr_identity != prev_identity:
                new_fields = {}
                for key in ["name", "age", "gender"]:
                    if curr_identity.get(key) and curr_identity.get(key) != prev_identity.get(key):
                        new_fields[key] = curr_identity.get(key)
                if new_fields:
                    turn_events.append(("Identity", new_fields))
                prev_identity = curr_identity.copy() if curr_identity else {}

            # Track Concerns changes
            curr_concerns = turn.gestalt_concerns or []
            if curr_concerns != prev_concerns:
                new_concerns = [c for c in curr_concerns if c not in prev_concerns]
                if new_concerns:
                    turn_events.append(("Concerns", new_concerns))
                prev_concerns = curr_concerns.copy() if curr_concerns else []

            # Track Strengths changes
            curr_strengths = turn.gestalt_strengths or []
            if curr_strengths != prev_strengths:
                new_strengths = [s for s in curr_strengths if s not in prev_strengths]
                if new_strengths:
                    turn_events.append(("Strengths", new_strengths))
                prev_strengths = curr_strengths.copy() if curr_strengths else []

            # Track Essence changes
            curr_essence = turn.gestalt_essence or {}
            if curr_essence != prev_essence:
                new_essence = {}
                for key, val in curr_essence.items():
                    if val and val != prev_essence.get(key):
                        new_essence[key] = val
                if new_essence:
                    turn_events.append(("Essence", new_essence))
                prev_essence = curr_essence.copy() if curr_essence else {}

            # Track Family changes
            curr_family = turn.gestalt_family or {}
            if curr_family != prev_family:
                new_family = {}
                for key, val in curr_family.items():
                    if val and val != prev_family.get(key):
                        new_family[key] = val
                if new_family:
                    turn_events.append(("Family", new_family))
                prev_family = curr_family.copy() if curr_family else {}

            # Track History changes
            curr_history = turn.gestalt_history or {}
            if curr_history != prev_history:
                new_history = {}
                for key, val in curr_history.items():
                    if val and val != prev_history.get(key):
                        new_history[key] = val
                if new_history:
                    turn_events.append(("History", new_history))
                prev_history = curr_history.copy() if curr_history else {}

            if turn_events:
                evolution_events.append((turn.turn, turn_events))

        # Generate narrative
        if not evolution_events:
            lines.append("*No gestalt evolution captured*")
            lines.append(f"")
            return lines

        for turn_num, events in evolution_events:
            # Determine the main theme for this turn
            themes = [e[0] for e in events]
            if "Identity" in themes:
                title = "Child Introduced"
            elif "Concerns" in themes and "Essence" in themes:
                title = "Patterns Forming"
            elif "Concerns" in themes:
                title = "Concerns Emerge"
            elif "Strengths" in themes:
                title = "Strengths Discovered"
            elif "Essence" in themes:
                title = "Core Qualities Emerging"
            elif "Family" in themes:
                title = "Family Context"
            elif "History" in themes:
                title = "History Revealed"
            else:
                title = "Understanding Deepens"

            lines.append(f"### Turn {turn_num}: {title}")
            lines.append(f"")

            for category, data in events:
                lines.append(f"**{category}:**")
                if isinstance(data, dict):
                    for key, val in data.items():
                        if isinstance(val, list):
                            lines.append(f"- {key}: {', '.join(str(v) for v in val)}")
                        else:
                            lines.append(f"- {key}: {val}")
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            item_str = ", ".join(f"{k}: {v}" for k, v in item.items() if v)
                            lines.append(f"- {item_str}")
                        else:
                            lines.append(f"- {item}")
                lines.append(f"")

        # Final Understanding Narrative
        final_turn = self.report.turns[-1] if self.report.turns else None
        if final_turn:
            lines.append(f"### Final Understanding Narrative")
            lines.append(f"")

            # Build narrative from final gestalt state
            narrative_parts = []

            if final_turn.gestalt_identity:
                identity = final_turn.gestalt_identity
                name = identity.get("name", "The child")
                age = identity.get("age")
                if age:
                    narrative_parts.append(f"{name} is {age} years old")

            if final_turn.gestalt_concerns:
                concerns = final_turn.gestalt_concerns
                if isinstance(concerns, list) and concerns:
                    concern_strs = []
                    for c in concerns[:3]:  # Limit to 3
                        if isinstance(c, dict):
                            concern_strs.append(c.get("description", c.get("area", str(c))))
                        else:
                            concern_strs.append(str(c))
                    narrative_parts.append(f"showing concerns in: {', '.join(concern_strs)}")

            if final_turn.gestalt_essence:
                essence = final_turn.gestalt_essence
                core_qualities = essence.get("core_qualities", [])
                if core_qualities:
                    if isinstance(core_qualities, list):
                        narrative_parts.append(f"with core qualities: {', '.join(str(q) for q in core_qualities[:2])}")

            if narrative_parts:
                lines.append(" ".join(narrative_parts) + ".")
            else:
                lines.append("*Understanding still developing*")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

        return lines

    def _generate_hypothesis_lifecycles(self) -> List[str]:
        """Generate lifecycle view for each hypothesis - tracking from formation to resolution"""
        lines = [
            f"## Hypothesis Lifecycles",
            f"",
            f"*Tracking the journey of each hypothesis from formation through evidence accumulation*",
            f"",
        ]

        # Collect all hypotheses across all turns with their history
        hypothesis_history: Dict[str, Dict] = {}

        for turn in self.report.turns:
            # Track hypothesis formations
            for event in turn.events:
                if event.category == "hypothesis":
                    h_id = event.related_ids.get("hypothesis_id", "")
                    if not h_id:
                        continue

                    if h_id not in hypothesis_history:
                        hypothesis_history[h_id] = {
                            "id": h_id,
                            "formation_turn": None,
                            "theory": "",
                            "domain": "",
                            "initial_confidence": 0,
                            "current_confidence": 0,
                            "status": "active",
                            "evidence_timeline": [],
                            "confidence_changes": [],
                            "questions": [],
                            "cycle_id": event.related_ids.get("cycle_id", ""),
                            "parent_trigger": turn.parent_message,
                        }

                    # Formation event
                    if "formed" in event.event_type.value.lower():
                        hypothesis_history[h_id]["formation_turn"] = turn.turn
                        hypothesis_history[h_id]["theory"] = event.details.get("theory", "")
                        hypothesis_history[h_id]["domain"] = event.details.get("domain", "")
                        hypothesis_history[h_id]["initial_confidence"] = event.details.get("confidence", 0)
                        hypothesis_history[h_id]["current_confidence"] = event.details.get("confidence", 0)
                        hypothesis_history[h_id]["questions"] = event.details.get("questions_to_explore", [])

                    # Evidence added
                    elif "evidence" in event.event_type.value.lower():
                        hypothesis_history[h_id]["evidence_timeline"].append({
                            "turn": turn.turn,
                            "content": event.details.get("evidence", ""),
                            "source": event.details.get("source", "parent"),
                            "effect": event.details.get("effect", "supports"),
                            "parent_quote": turn.parent_message[:60] + "..." if len(turn.parent_message) > 60 else turn.parent_message
                        })

                    # Confidence change
                    elif "confidence" in event.event_type.value.lower():
                        old_conf = event.details.get("old_confidence", 0)
                        new_conf = event.details.get("new_confidence", 0)
                        hypothesis_history[h_id]["confidence_changes"].append({
                            "turn": turn.turn,
                            "old": old_conf,
                            "new": new_conf,
                            "reason": event.details.get("reason", "")
                        })
                        hypothesis_history[h_id]["current_confidence"] = new_conf

                    # Resolution
                    elif "resolved" in event.event_type.value.lower():
                        hypothesis_history[h_id]["status"] = "resolved"
                        hypothesis_history[h_id]["resolution"] = event.details.get("resolution", "")
                        hypothesis_history[h_id]["resolution_turn"] = turn.turn

            # Also check hypotheses_summary for current state
            for h_summary in turn.hypotheses_summary:
                h_id = h_summary.get("id", "")
                if h_id in hypothesis_history:
                    hypothesis_history[h_id]["current_confidence"] = h_summary.get("confidence", 0)
                    hypothesis_history[h_id]["status"] = h_summary.get("status", "active")

        # Render each hypothesis lifecycle
        if not hypothesis_history:
            lines.append("*No hypotheses formed during this conversation*")
            lines.append("")
            return lines

        for h_id, h_data in hypothesis_history.items():
            short_id = h_id[:8] if len(h_id) > 8 else h_id
            status_icon = "✅" if h_data["status"] == "resolved" else "🔄"

            lines.append(f"### {status_icon} Hypothesis `{short_id}`")
            lines.append(f"")

            # Theory
            theory = h_data.get("theory", "Unknown theory")
            lines.append(f"**Theory:** \"{theory}\"")
            lines.append(f"")

            # Formation details
            lines.append(f"#### Formation (Turn {h_data.get('formation_turn', '?')})")
            lines.append(f"")
            trigger = h_data.get("parent_trigger", "")
            if trigger:
                trigger_short = trigger[:80] + "..." if len(trigger) > 80 else trigger
                lines.append(f"- **Trigger:** \"{trigger_short}\"")
            lines.append(f"- **Domain:** {h_data.get('domain', 'unknown')}")
            initial_conf = h_data.get("initial_confidence", 0)
            lines.append(f"- **Initial Confidence:** {initial_conf:.0%}")
            if h_data.get("questions"):
                lines.append(f"- **Questions to Explore:**")
                for q in h_data["questions"][:3]:
                    lines.append(f"  - {q}")
            lines.append(f"")

            # Evidence accumulation table
            evidence_timeline = h_data.get("evidence_timeline", [])
            if evidence_timeline:
                lines.append(f"#### Evidence Accumulation")
                lines.append(f"")
                lines.append(f"| Turn | Evidence | Source | Effect |")
                lines.append(f"|------|----------|--------|--------|")
                for ev in evidence_timeline:
                    content = ev.get("content", "")[:50]
                    if len(ev.get("content", "")) > 50:
                        content += "..."
                    effect = ev.get("effect", "supports").upper()
                    lines.append(f"| {ev['turn']} | {content} | {ev['source']} | {effect} |")
                lines.append(f"")

            # Confidence journey
            conf_changes = h_data.get("confidence_changes", [])
            if conf_changes:
                lines.append(f"#### Confidence Journey")
                lines.append(f"")
                conf_line = f"{h_data.get('initial_confidence', 0):.0%}"
                for change in conf_changes:
                    arrow = "↑" if change["new"] > change["old"] else "↓" if change["new"] < change["old"] else "→"
                    conf_line += f" {arrow} {change['new']:.0%} (Turn {change['turn']})"
                lines.append(f"```")
                lines.append(conf_line)
                lines.append(f"```")
                lines.append(f"")

            # Current status
            lines.append(f"#### Current Status")
            lines.append(f"")
            lines.append(f"- **Status:** {h_data['status']}")
            lines.append(f"- **Confidence:** {h_data['current_confidence']:.0%}")
            if h_data.get("resolution"):
                lines.append(f"- **Resolution:** {h_data['resolution']}")
            if h_data.get("cycle_id"):
                lines.append(f"- **Cycle:** `{h_data['cycle_id'][:8]}`")
            lines.append(f"")

            lines.append(f"---")
            lines.append(f"")

        return lines

    def _generate_cross_cycle_connections(self) -> List[str]:
        """Generate a map showing how cycles and hypotheses connect across domains"""
        lines = [
            f"## Cross-Cycle Connection Map",
            f"",
            f"*Visualizing how separate concerns reveal underlying patterns*",
            f"",
        ]

        # Collect cycles by domain with their hypotheses
        cycles_by_domain: Dict[str, Dict] = {}
        patterns_detected: List[Dict] = []

        for turn in self.report.turns:
            # Collect cycle information
            for cycle in turn.exploration_cycles:
                domain = cycle.get("focus_domain", "unknown")
                cycle_id = cycle.get("id", "")

                if domain not in cycles_by_domain:
                    cycles_by_domain[domain] = {
                        "domain": domain,
                        "first_turn": turn.turn,
                        "cycle_ids": [],
                        "hypotheses": [],
                        "key_evidence": []
                    }

                if cycle_id and cycle_id not in cycles_by_domain[domain]["cycle_ids"]:
                    cycles_by_domain[domain]["cycle_ids"].append(cycle_id)

            # Collect hypotheses for each domain
            for h in turn.hypotheses_summary:
                domain = h.get("domain", "unknown")
                if domain in cycles_by_domain:
                    h_exists = any(
                        existing.get("id") == h.get("id")
                        for existing in cycles_by_domain[domain]["hypotheses"]
                    )
                    if not h_exists:
                        cycles_by_domain[domain]["hypotheses"].append(h)

            # Collect pattern detections
            for event in turn.events:
                if event.category == "pattern":
                    patterns_detected.append({
                        "turn": turn.turn,
                        "theme": event.details.get("theme", ""),
                        "description": event.details.get("description", ""),
                        "domains": event.details.get("domains_involved", []),
                        "confidence": event.details.get("confidence", 0)
                    })

        # Render domain boxes
        if not cycles_by_domain:
            lines.append("*No exploration cycles created during this conversation*")
            lines.append("")
            return lines

        lines.append("### Domain Overview")
        lines.append("")

        for domain, data in cycles_by_domain.items():
            domain_upper = domain.upper() if domain else "UNKNOWN"
            lines.append(f"#### {domain_upper} (First seen: Turn {data['first_turn']})")
            lines.append("")

            # Show hypotheses in this domain
            if data["hypotheses"]:
                lines.append("**Hypotheses:**")
                for h in data["hypotheses"]:
                    status_icon = "✅" if h.get("status") == "resolved" else "🔄"
                    conf = h.get("confidence", 0)
                    theory = h.get("theory", "")[:60]
                    if len(h.get("theory", "")) > 60:
                        theory += "..."
                    lines.append(f"- {status_icon} {theory} ({conf:.0%})")
            else:
                lines.append("*No hypotheses yet*")

            lines.append("")

        # Show cross-cycle patterns if any
        if patterns_detected:
            lines.append("### Cross-Cycle Patterns Detected")
            lines.append("")

            for pattern in patterns_detected:
                lines.append(f"#### Pattern: \"{pattern['theme']}\"")
                lines.append(f"")
                lines.append(f"- **Detected:** Turn {pattern['turn']}")
                lines.append(f"- **Domains Involved:** {', '.join(pattern['domains']) if pattern['domains'] else 'N/A'}")
                lines.append(f"- **Confidence:** {pattern['confidence']:.0%}")
                if pattern['description']:
                    lines.append(f"- **Description:** {pattern['description']}")
                lines.append(f"")

        # Generate connection diagram (simplified ASCII)
        if len(cycles_by_domain) > 1:
            lines.append("### Connection Diagram")
            lines.append("")
            lines.append("```")

            domains = list(cycles_by_domain.keys())
            # Show connections between domains
            for i, domain in enumerate(domains):
                box_width = 20
                domain_upper = domain.upper()[:18]
                lines.append(f"┌{'─' * box_width}┐")
                lines.append(f"│ {domain_upper:^{box_width - 2}} │")
                lines.append(f"│ Turn {cycles_by_domain[domain]['first_turn']:<{box_width - 7}} │")
                h_count = len(cycles_by_domain[domain]['hypotheses'])
                lines.append(f"│ {h_count} hypothesis{'es' if h_count != 1 else '':<{box_width - 14}} │")
                lines.append(f"└{'─' * box_width}┘")

                if i < len(domains) - 1:
                    lines.append(f"        │")
                    lines.append(f"        ▼")

            lines.append("```")
            lines.append("")

        # Narrative synthesis
        lines.append("### Emerging Narrative")
        lines.append("")

        if patterns_detected:
            # Use detected patterns to form narrative
            themes = [p["theme"] for p in patterns_detected if p["theme"]]
            if themes:
                narrative = f"Patterns detected: {', '.join(themes)}. "
                domains_involved = set()
                for p in patterns_detected:
                    domains_involved.update(p.get("domains", []))
                if domains_involved:
                    narrative += f"These connect the {', '.join(domains_involved)} domains."
                lines.append(f"> {narrative}")
            else:
                lines.append("> *Patterns are forming but not yet articulated*")
        elif len(cycles_by_domain) > 1:
            domains_list = list(cycles_by_domain.keys())
            lines.append(f"> Multiple domains explored ({', '.join(domains_list)}). Connections may emerge as understanding deepens.")
        else:
            lines.append("> *Single domain exploration - connections will emerge as more areas are explored*")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _generate_memory_evolution(self) -> List[str]:
        """Generate a view of how conversation memory (the 'slow brain') evolves across turns.

        Shows when reflections happen and how parent/child understanding develops over time.
        """
        lines = [
            f"## Memory Evolution",
            f"",
            f"*Tracking how Chitta's understanding of the parent and conversation develops (the 'slow brain')*",
            f"",
        ]

        # Track memory changes across turns
        memory_snapshots = []
        prev_memory = {}

        for turn in self.report.turns:
            if turn.conversation_memory:
                memory = turn.conversation_memory.get("memory", {})
                last_reflection = turn.conversation_memory.get("last_reflection_turn", 0)
                needs_reflection = turn.conversation_memory.get("needs_reflection", False)

                # Check if memory changed
                memory_changed = memory != prev_memory

                if memory or memory_changed:
                    memory_snapshots.append({
                        "turn": turn.turn,
                        "memory": memory,
                        "last_reflection": last_reflection,
                        "needs_reflection": needs_reflection,
                        "changed": memory_changed
                    })
                    prev_memory = memory.copy() if memory else {}

        if not memory_snapshots:
            lines.append("*No memory reflections recorded during this conversation*")
            lines.append("")
            lines.append("---")
            lines.append("")
            return lines

        # Group by reflection events
        reflection_turns = []
        for snap in memory_snapshots:
            if snap["changed"]:
                reflection_turns.append(snap)

        if reflection_turns:
            lines.append("### Reflection Events")
            lines.append("")

            for snap in reflection_turns:
                turn_num = snap["turn"]
                memory = snap["memory"]

                lines.append(f"#### Turn {turn_num}: Memory Updated")
                lines.append("")

                # Parent style observations
                parent_style = memory.get("parent_style", "")
                if parent_style:
                    lines.append(f"**Parent Style Observed:**")
                    lines.append(f"> {parent_style}")
                    lines.append("")

                # Emotional patterns
                emotional = memory.get("emotional_pattern", "")
                if emotional:
                    lines.append(f"**Emotional Pattern:**")
                    lines.append(f"> {emotional}")
                    lines.append("")

                # Topics discussed
                topics = memory.get("topics_discussed", [])
                if topics:
                    lines.append(f"**Topics Covered:** {', '.join(topics)}")
                    lines.append("")

                # Key observations
                observations = memory.get("key_observations", [])
                if observations:
                    lines.append(f"**Key Observations:**")
                    for obs in observations:
                        lines.append(f"- {obs}")
                    lines.append("")

                # Rapport notes
                rapport = memory.get("rapport_notes", "")
                if rapport:
                    lines.append(f"**Rapport Notes:**")
                    lines.append(f"> {rapport}")
                    lines.append("")

                # Vocabulary learned
                vocabulary = memory.get("vocabulary", [])
                if vocabulary:
                    lines.append(f"**Parent Vocabulary:** {', '.join(vocabulary)}")
                    lines.append("")

        # Current memory state summary
        if memory_snapshots:
            last_snap = memory_snapshots[-1]
            memory = last_snap["memory"]

            if memory:
                lines.append("### Current Memory State")
                lines.append("")
                lines.append("```")

                # Format memory as readable summary
                parent_style = memory.get("parent_style", "Unknown")
                lines.append(f"Parent Style: {parent_style}")

                topics = memory.get("topics_discussed", [])
                if topics:
                    lines.append(f"Topics: {', '.join(topics)}")

                emotional = memory.get("emotional_pattern", "")
                if emotional:
                    lines.append(f"Emotional Tone: {emotional}")

                rapport = memory.get("rapport_notes", "")
                if rapport:
                    lines.append(f"Rapport: {rapport}")

                vocabulary = memory.get("vocabulary", [])
                if vocabulary:
                    lines.append(f"Vocabulary: {', '.join(vocabulary[:5])}")  # Limit to 5

                lines.append("```")
                lines.append("")

        # Memory evolution summary
        lines.append("### Evolution Summary")
        lines.append("")

        total_reflections = len(reflection_turns)
        if total_reflections == 0:
            lines.append("> No reflections occurred during this conversation - memory remained static")
        elif total_reflections == 1:
            lines.append(f"> Single reflection at turn {reflection_turns[0]['turn']}")
        else:
            reflection_turn_nums = [str(r["turn"]) for r in reflection_turns]
            lines.append(f"> {total_reflections} reflections occurred at turns: {', '.join(reflection_turn_nums)}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _generate_html_dashboard(self) -> str:
        """Generate interactive HTML dashboard with drill-down navigation.

        Feature 6 from the X-Ray Dashboard redesign plan.
        Provides clickable navigation from:
        - Emergence Timeline → Turn Detail → Hypothesis Lifecycle → Evidence
        """
        import json as json_module

        # Prepare data for JavaScript
        turns_data = []
        for turn in self.report.turns:
            turn_data = {
                "turn": turn.turn,
                "parent_message": turn.parent_message,
                "chitta_response": turn.chitta_response,
                "completeness": turn.completeness,
                "active_cycles": turn.active_cycles_count,
                "hypotheses_count": turn.hypotheses_count,
                "tool_calls": turn.tool_calls,
                "events": [
                    {
                        "type": e.event_type.value if hasattr(e.event_type, 'value') else str(e.event_type),
                        "category": e.category,
                        "summary": e.summary,
                        "details": e.details,
                        "related_ids": e.related_ids
                    }
                    for e in turn.events
                ],
                "hypotheses": turn.hypotheses_summary,
                "cycles": turn.exploration_cycles
            }
            turns_data.append(turn_data)

        # Collect all hypotheses for lifecycle view
        all_hypotheses = {}
        for turn in self.report.turns:
            for event in turn.events:
                if event.category == "hypothesis":
                    h_id = event.related_ids.get("hypothesis_id", "")
                    if h_id and h_id not in all_hypotheses:
                        all_hypotheses[h_id] = {
                            "id": h_id,
                            "formation_turn": turn.turn,
                            "theory": event.details.get("theory", ""),
                            "domain": event.details.get("domain", ""),
                            "confidence": event.details.get("confidence", 0),
                            "events": []
                        }
                    if h_id:
                        all_hypotheses[h_id]["events"].append({
                            "turn": turn.turn,
                            "type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                            "details": event.details,
                            "parent_message": turn.parent_message
                        })

        html = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chitta X-Ray Dashboard - {self.report.session_id}</title>
    <style>
        :root {{
            --primary: #4a90a4;
            --secondary: #6b7280;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg-light: #f9fafb;
            --bg-card: #ffffff;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --border: #e5e7eb;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-light);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            background: var(--bg-card);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: var(--primary);
            font-size: 1.5rem;
            margin-bottom: 10px;
        }}

        .meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: var(--bg-card);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
        }}

        .stat-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .main-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        @media (max-width: 1000px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
        }}

        .panel {{
            background: var(--bg-card);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .panel-header {{
            background: var(--primary);
            color: white;
            padding: 15px 20px;
            font-weight: 600;
        }}

        .panel-content {{
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
        }}

        .turn-card {{
            background: var(--bg-light);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .turn-card:hover {{
            border-color: var(--primary);
            box-shadow: 0 2px 8px rgba(74, 144, 164, 0.2);
        }}

        .turn-card.active {{
            border-color: var(--primary);
            background: rgba(74, 144, 164, 0.1);
        }}

        .turn-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .turn-number {{
            background: var(--primary);
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }}

        .turn-metrics {{
            display: flex;
            gap: 10px;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .metric {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .parent-quote {{
            font-style: italic;
            color: var(--text-secondary);
            margin-bottom: 8px;
            font-size: 0.95rem;
        }}

        .discovery {{
            font-size: 0.9rem;
            color: var(--text-primary);
        }}

        .detail-panel {{
            display: none;
        }}

        .detail-panel.active {{
            display: block;
        }}

        .flow-box {{
            background: var(--bg-light);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }}

        .flow-box-title {{
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .flow-arrow {{
            text-align: center;
            color: var(--primary);
            font-size: 1.5rem;
            margin: 5px 0;
        }}

        .hypothesis-card {{
            background: linear-gradient(135deg, rgba(74, 144, 164, 0.1), rgba(74, 144, 164, 0.05));
            border: 1px solid var(--primary);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: pointer;
        }}

        .hypothesis-card:hover {{
            box-shadow: 0 2px 8px rgba(74, 144, 164, 0.3);
        }}

        .hypothesis-theory {{
            font-weight: 500;
            margin-bottom: 8px;
        }}

        .hypothesis-meta {{
            display: flex;
            gap: 15px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .confidence-bar {{
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            margin-top: 8px;
            overflow: hidden;
        }}

        .confidence-fill {{
            height: 100%;
            background: var(--success);
            border-radius: 3px;
            transition: width 0.3s;
        }}

        .evidence-item {{
            padding: 10px;
            background: var(--bg-light);
            border-right: 3px solid var(--success);
            margin-bottom: 8px;
            font-size: 0.9rem;
        }}

        .evidence-item.refines {{
            border-right-color: var(--warning);
        }}

        .evidence-item.contradicts {{
            border-right-color: var(--danger);
        }}

        .tool-call {{
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }}

        .tool-name {{
            font-weight: 600;
            color: #0369a1;
        }}

        .tool-args {{
            margin-top: 5px;
            color: var(--text-secondary);
            font-family: monospace;
            font-size: 0.8rem;
        }}

        .breadcrumb {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            font-size: 0.9rem;
        }}

        .breadcrumb a {{
            color: var(--primary);
            text-decoration: none;
            cursor: pointer;
        }}

        .breadcrumb a:hover {{
            text-decoration: underline;
        }}

        .state-delta {{
            background: #f0fdf4;
            border: 1px solid #86efac;
            border-radius: 6px;
            padding: 10px;
            margin-top: 15px;
        }}

        .delta-title {{
            font-weight: 600;
            color: #166534;
            margin-bottom: 5px;
        }}

        .delta-item {{
            font-size: 0.85rem;
            color: #166534;
        }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }}

        .empty-state-icon {{
            font-size: 3rem;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 Chitta X-Ray Dashboard</h1>
            <div class="meta">
                <span>📋 Session: {self.report.session_id}</span>
                <span>👨‍👩‍👧 Family: {self.report.family_id}</span>
                <span>🕐 {self.report.generated_at.strftime('%Y-%m-%d %H:%M') if self.report.generated_at else 'N/A'}</span>
                <span>🎭 Scenario: {self.report.scenario}</span>
            </div>
        </header>

        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value">{self.report.total_turns}</div>
                <div class="stat-label">Total Turns</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.report.total_events}</div>
                <div class="stat-label">Events Captured</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.report.cycles_created}</div>
                <div class="stat-label">Cycles Created</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.report.hypotheses_formed}</div>
                <div class="stat-label">Hypotheses Formed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.report.hypotheses_resolved}</div>
                <div class="stat-label">Hypotheses Resolved</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.report.artifacts_created}</div>
                <div class="stat-label">Artifacts Created</div>
            </div>
        </div>

        <div class="main-content">
            <div class="panel">
                <div class="panel-header">📈 Emergence Timeline</div>
                <div class="panel-content" id="timeline-panel">
                    <!-- Turns will be rendered here -->
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">🔍 Detail View</div>
                <div class="panel-content" id="detail-panel">
                    <div class="empty-state">
                        <div class="empty-state-icon">👆</div>
                        <p>Click on a turn to see the causation flow</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Data from Python
        const turnsData = {json_module.dumps(turns_data, ensure_ascii=False, default=str)};
        const hypothesesData = {json_module.dumps(all_hypotheses, ensure_ascii=False, default=str)};

        // Render timeline
        function renderTimeline() {{
            const panel = document.getElementById('timeline-panel');
            let html = '';

            turnsData.forEach((turn, idx) => {{
                const prevTurn = idx > 0 ? turnsData[idx - 1] : null;
                const completenessChange = prevTurn
                    ? (turn.completeness - prevTurn.completeness) * 100
                    : turn.completeness * 100;

                // Determine what was discovered this turn
                let discovery = '';
                const toolCalls = turn.tool_calls || [];
                const events = turn.events || [];

                // Check for significant events
                const cycleEvents = events.filter(e => e.category === 'cycle');
                const hypothesisEvents = events.filter(e => e.category === 'hypothesis');
                const patternEvents = events.filter(e => e.category === 'pattern');

                if (cycleEvents.length > 0) {{
                    discovery += '🔄 New cycle opened. ';
                }}
                if (hypothesisEvents.length > 0) {{
                    discovery += '💡 Hypothesis formed. ';
                }}
                if (patternEvents.length > 0) {{
                    discovery += '🔗 Pattern detected. ';
                }}
                if (!discovery && toolCalls.length > 0) {{
                    discovery = '📝 Information extracted';
                }}
                if (!discovery) {{
                    discovery = '💬 Conversation continued';
                }}

                html += `
                    <div class="turn-card" onclick="showTurnDetail(${{turn.turn}})" data-turn="${{turn.turn}}">
                        <div class="turn-header">
                            <span class="turn-number">Turn ${{turn.turn}}</span>
                            <div class="turn-metrics">
                                <span class="metric">📊 ${{(turn.completeness * 100).toFixed(1)}}%</span>
                                <span class="metric">🔄 ${{turn.active_cycles}}</span>
                                <span class="metric">💡 ${{turn.hypotheses_count}}</span>
                            </div>
                        </div>
                        <div class="parent-quote">"${{truncate(turn.parent_message, 60)}}"</div>
                        <div class="discovery">${{discovery}}</div>
                    </div>
                `;
            }});

            panel.innerHTML = html;
        }}

        // Show turn detail with causation flow
        function showTurnDetail(turnNum) {{
            const turn = turnsData.find(t => t.turn === turnNum);
            if (!turn) return;

            // Update active state
            document.querySelectorAll('.turn-card').forEach(card => {{
                card.classList.toggle('active', card.dataset.turn == turnNum);
            }});

            const panel = document.getElementById('detail-panel');
            let html = `
                <div class="breadcrumb">
                    <a onclick="showOverview()">Overview</a> →
                    <span>Turn ${{turnNum}}</span>
                </div>
            `;

            // Parent input box
            html += `
                <div class="flow-box">
                    <div class="flow-box-title">👤 Parent Input</div>
                    <div>"${{turn.parent_message}}"</div>
                </div>
                <div class="flow-arrow">▼</div>
            `;

            // Tool calls (grouped by type)
            const toolCalls = turn.tool_calls || [];
            if (toolCalls.length > 0) {{
                html += `
                    <div class="flow-box">
                        <div class="flow-box-title">⚙️ Processing (${{toolCalls.length}} tool calls)</div>
                `;
                toolCalls.forEach(tc => {{
                    const toolName = tc.tool || 'unknown';
                    const args = tc.arguments || {{}};
                    html += `
                        <div class="tool-call">
                            <div class="tool-name">${{toolName}}</div>
                            <div class="tool-args">${{JSON.stringify(args).substring(0, 100)}}...</div>
                        </div>
                    `;
                }});
                html += `</div><div class="flow-arrow">▼</div>`;
            }}

            // Hypotheses formed this turn
            const hypothesisEvents = (turn.events || []).filter(e => e.category === 'hypothesis');
            if (hypothesisEvents.length > 0) {{
                html += `
                    <div class="flow-box">
                        <div class="flow-box-title">💡 Hypotheses</div>
                `;
                hypothesisEvents.forEach(event => {{
                    const hId = event.related_ids?.hypothesis_id || '';
                    const theory = event.details?.theory || event.summary || '';
                    const confidence = event.details?.confidence || 0;
                    html += `
                        <div class="hypothesis-card" onclick="showHypothesisDetail('${{hId}}')">
                            <div class="hypothesis-theory">${{theory}}</div>
                            <div class="hypothesis-meta">
                                <span>Domain: ${{event.details?.domain || 'N/A'}}</span>
                                <span>Confidence: ${{(confidence * 100).toFixed(0)}}%</span>
                            </div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${{confidence * 100}}%"></div>
                            </div>
                        </div>
                    `;
                }});
                html += `</div><div class="flow-arrow">▼</div>`;
            }}

            // Chitta response
            html += `
                <div class="flow-box">
                    <div class="flow-box-title">🤖 Chitta Response</div>
                    <div style="white-space: pre-wrap;">${{turn.chitta_response}}</div>
                </div>
            `;

            // State delta
            const prevTurn = turnsData.find(t => t.turn === turnNum - 1);
            if (prevTurn) {{
                const completenessChange = ((turn.completeness - prevTurn.completeness) * 100).toFixed(2);
                const cyclesChange = turn.active_cycles - prevTurn.active_cycles;
                const hypothesesChange = turn.hypotheses_count - prevTurn.hypotheses_count;

                if (completenessChange != 0 || cyclesChange != 0 || hypothesesChange != 0) {{
                    html += `
                        <div class="state-delta">
                            <div class="delta-title">📊 State Changes</div>
                    `;
                    if (completenessChange != 0) {{
                        html += `<div class="delta-item">Completeness: ${{prevTurn.completeness * 100}}% → ${{turn.completeness * 100}}% (${{completenessChange > 0 ? '+' : ''}}${{completenessChange}}%)</div>`;
                    }}
                    if (cyclesChange != 0) {{
                        html += `<div class="delta-item">Active Cycles: ${{prevTurn.active_cycles}} → ${{turn.active_cycles}} (${{cyclesChange > 0 ? '+' : ''}}${{cyclesChange}})</div>`;
                    }}
                    if (hypothesesChange != 0) {{
                        html += `<div class="delta-item">Hypotheses: ${{prevTurn.hypotheses_count}} → ${{turn.hypotheses_count}} (${{hypothesesChange > 0 ? '+' : ''}}${{hypothesesChange}})</div>`;
                    }}
                    html += `</div>`;
                }}
            }}

            panel.innerHTML = html;
        }}

        // Show hypothesis lifecycle detail
        function showHypothesisDetail(hId) {{
            const hypothesis = hypothesesData[hId];
            if (!hypothesis) return;

            const panel = document.getElementById('detail-panel');
            let html = `
                <div class="breadcrumb">
                    <a onclick="showOverview()">Overview</a> →
                    <a onclick="showTurnDetail(${{hypothesis.formation_turn}})">Turn ${{hypothesis.formation_turn}}</a> →
                    <span>Hypothesis ${{hId.substring(0, 8)}}</span>
                </div>

                <div class="flow-box">
                    <div class="flow-box-title">📋 Hypothesis: ${{hId.substring(0, 8)}}</div>
                    <div class="hypothesis-theory">${{hypothesis.theory}}</div>
                    <div class="hypothesis-meta" style="margin-top: 10px;">
                        <span>Domain: ${{hypothesis.domain}}</span>
                        <span>Formed: Turn ${{hypothesis.formation_turn}}</span>
                    </div>
                </div>
            `;

            // Evidence timeline
            const events = hypothesis.events || [];
            if (events.length > 0) {{
                html += `
                    <div class="flow-box">
                        <div class="flow-box-title">📜 Event History</div>
                `;
                events.forEach(event => {{
                    const eventType = event.type || '';
                    let cssClass = 'evidence-item';
                    if (eventType.includes('refine')) cssClass += ' refines';
                    if (eventType.includes('contradict')) cssClass += ' contradicts';

                    html += `
                        <div class="${{cssClass}}">
                            <strong>Turn ${{event.turn}}:</strong> ${{eventType}}<br>
                            <em>"${{truncate(event.parent_message, 80)}}"</em>
                        </div>
                    `;
                }});
                html += `</div>`;
            }}

            panel.innerHTML = html;
        }}

        // Show overview
        function showOverview() {{
            const panel = document.getElementById('detail-panel');
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">👆</div>
                    <p>Click on a turn to see the causation flow</p>
                </div>
            `;
            document.querySelectorAll('.turn-card').forEach(card => card.classList.remove('active'));
        }}

        // Helper function to truncate text
        function truncate(text, maxLength) {{
            if (!text) return '';
            return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
        }}

        // Initialize
        renderTimeline();
    </script>
</body>
</html>'''

        return html

    def save_html_dashboard(self, output_path: Optional[str] = None) -> str:
        """Save the interactive HTML dashboard to a file.

        Args:
            output_path: Optional path for the HTML file. If not provided,
                        uses the same directory as other outputs with .html extension.

        Returns:
            Path to the saved HTML file.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                self.output_dir,
                f"xray_{self.report.scenario}_{timestamp}.html"
            )

        html_content = self._generate_html_dashboard()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path


# === Predefined Scenarios ===
# NOTE: Context labels describe what info the parent shares, NOT what Chitta asked.
# This keeps scenarios faithful to the actual conversational flow.

SCENARIOS = {
    # Extended scenario with 18 turns for comprehensive cycle resolution testing
    "scattered_parent": [
        ("Shares: Referred here", "שלום, קיבלתי המלצה לפנות אליכם"),
        ("Shares: Has a son, worried", "יש לי בן, אני קצת מודאגת ממנו"),
        ("Shares: Name (Yoav), age (4)", "הוא בן 4, קוראים לו יואב. אני לא יודעת איך להסביר..."),
        ("Shares: Different from peers", "הוא פשוט לא כמו הילדים האחרים בגן. משהו שונה אצלו"),
        ("Shares: Morning struggles + social", "בבוקר זה סיוט להוציא אותו. והוא לא משחק עם ילדים אחרים בכלל"),
        ("Shares: TV tantrums", "הוא לא רוצה להפסיק עם הטלוויזיה. עושה סצנות נוראיות"),
        ("Shares: Contradicts - transitions OK when motivated", "אבל כשהוא רוצה משהו הוא עובר מעברים בלי בעיה. אולי אני מגזימה?"),
        ("Shares: Sits alone, no interest in peers", "מה שבאמת מדאיג אותי זה שהוא לא מתעניין בחברים. יושב לבד"),
        ("Shares: Noise sensitivity", "עכשיו שאני חושבת על זה, גם רעשים חזקים מאוד מפריעים לו"),
        ("Shares: Self-doubt about concerns", "אני לא יודעת אם כל הדברים האלה קשורים או שאני סתם מחפשת בעיות"),
        # Extended turns for cycle resolution
        ("Shares: Strengths - dinosaurs, space", "אבל הוא ילד כל כך חכם! יודע את כל הדינוזאורים והכוכבים"),
        ("Shares: Deep focus on space books", "הוא יכול לשבת שעות ולקרוא ספרים על חלל. זה מטורף"),
        ("Shares: Plays with one neighbor only", "הוא כן משחק עם הילדה מהקומה למעלה לפעמים. רק אתה, לא בקבוצה"),
        ("Shares: Better with routine", "כשיש לו לוח זמנים קבוע הוא הרבה יותר רגוע. שבת הכי קשה"),
        ("Shares: Realizes noise-kindergarten connection", "עכשיו שאני מספרת לך את זה, אני מבינה שהרעש בגן בטח מאוד מציק לו"),
        ("Asks: Is solo play for quiet?", "זה הגיוני שהוא מעדיף לשחק לבד? כי ככה שקט לו?"),
        ("Asks: How to help at kindergarten?", "אז מה לעשות? איך אני עוזרת לו בגן?"),
        ("Agrees: Will film morning transition", "כן, אשמח לצלם אותו בבוקר כשהוא צריך לעזוב את הבית"),
    ],

    "video_workflow": [
        ("Shares: Daughter Maya, 3.5yo", "שלום, יש לי בת בת 3 וחצי, קוראים לה מאיה"),
        ("Shares: Falls often, wandering", "היא נופלת הרבה, קשה לה עם מדרגות ולפעמים נראה שהיא מסתובבת בלי מטרה"),
        ("Shares: Hard to describe in words", "קשה לי להסביר את זה במילים, זה משהו שצריך לראות"),
        ("Agrees: Will film, asks how", "כן, אשמח לצלם אותה! איך עושים את זה?"),
        ("Shares: Got guidelines, will film", "קיבלתי את ההנחיות, אצלם היום אחר הצהריים"),
        # Extended video workflow
        ("Shares: Filmed and uploading", "צילמתי אותה היום, מעלה עכשיו"),
        ("Asks: When will I get feedback?", "מה הלאה? מתי אקבל משוב?"),
        ("Shares: Tires quickly outside", "היא גם מתעייפת מהר מאוד כשמשחקים בחוץ, זה קשור?"),
    ],

    "multi_domain": [
        ("Shares: Son Or, age 5", "שלום, הבן שלי אור בן 5"),
        ("Shares: Unclear speech", "הוא עדיין מדבר לא ברור, אנשים לא מבינים אותו"),
        ("Shares: Mostly alone at kindergarten", "גם בגן הוא בעיקר לבד, לא משחק עם הילדים האחרים"),
        ("Shares: Covers ears, clothing sensitivity", "הוא גם מכסה את האוזניים כשיש רעש, ולא אוהב בגדים מסוימים"),
        ("Shares: Difficulty with writing/drawing", "ולעניין של כתיבה וציור הוא עדיין לא מצליח טוב"),
        ("Asks: Should we get him checked?", "רציתי לשאול, אולי כדאי לבדוק אותו? מה דעתכם?"),
        # Extended multi-domain
        ("Shares: Similar childhood (parent)", "גם אני הייתי ילד שקט בגן, כזה שמעדיף לבד"),
        ("Shares: Good at lego/puzzles", "אבל הוא ממש טוב בלגו ובפאזלים. יכול לעשות פאזלים של ילדים גדולים"),
        ("Shares: Few words, mostly single words", "הוא לא אומר כל כך הרבה מילים בכלל. עיקר השפה זה מילים בודדות"),
        ("Shares: Gets frustrated quickly", "הוא גם מתסכל מהר כשמשהו לא מצליח לו"),
        ("Shares: Younger sister talks better", "האחות הקטנה שלו כבר מדברת יותר טוב ממנו והיא רק בת 2"),
        ("Asks: Which specialist to see?", "מה אתם חושבים? לאיזה מומחה כדאי לפנות?"),
    ],

    # Short scenario for quick testing
    "quick_test": [
        ("Shares: Son Daniel, age 3", "שלום, הילד שלי דניאל בן 3"),
        ("Shares: Not talking yet, few words", "הוא לא מדבר עדיין. רק כמה מילים"),
        ("Shares: Understands but doesn't speak", "הוא מבין הכל, אבל לא משתמש במילים"),
    ],
}


def main():
    parser = argparse.ArgumentParser(description="Chitta Temporal Design X-Ray Test")
    parser.add_argument("--scenario", default="scattered_parent",
                        choices=list(SCENARIOS.keys()),
                        help="Scenario to run")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help="Output directory for reports")
    parser.add_argument("--base-url", default=BASE_URL,
                        help="Base URL for Chitta API")
    args = parser.parse_args()

    # Run test
    tester = ChittaXRayTest(base_url=args.base_url, output_dir=args.output_dir)
    messages = SCENARIOS[args.scenario]

    report = tester.run_scenario(args.scenario, messages)
    paths = tester.save_report()

    print(f"\n{'='*80}")
    print(f"  X-RAY TEST COMPLETE")
    print(f"{'='*80}")
    print(f"\nAnalytics:")
    print(f"  - Total events captured: {report.total_events}")
    print(f"  - Cycles created: {report.cycles_created}")
    print(f"  - Hypotheses formed: {report.hypotheses_formed}")
    print(f"  - Hypotheses resolved: {report.hypotheses_resolved}")
    print(f"  - Artifacts created: {report.artifacts_created}")
    print(f"\nFiles saved:")
    print(f"  - JSON: {paths['json']}")
    print(f"  - Markdown: {paths['markdown']}")


if __name__ == "__main__":
    main()
