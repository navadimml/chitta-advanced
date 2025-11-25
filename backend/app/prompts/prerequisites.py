"""
DEPRECATED: This file contained legacy enum-based prerequisite system.

🌟 Wu Wei Architecture Migration:

The prerequisite system has been completely refactored to be configuration-driven:

**Old System (REMOVED):**
- Action and PrerequisiteType enums
- Hardcoded PREREQUISITES dict
- Completeness thresholds (>= 80%)
- Phase-based logic

**New System (Current):**
1. **action_graph.yaml** - Defines actions and their prerequisites
2. **lifecycle_events.yaml** - Defines workflow moments and when they trigger
3. **wu_wei_prerequisites.py** - Qualitative prerequisite evaluation (knowledge richness)
4. **action_registry.py** - Config-driven action availability checking
5. **prerequisite_service.py** - Thin wrapper for convenience

**Key Changes:**
- Prerequisites are string IDs (not enums): "knowledge_is_rich", "has_baseline_video_guidelines", etc.
- Actions are string IDs (not enums): "view_video_guidelines", "upload_video", etc.
- No hardcoded thresholds - qualitative checks instead
- No phases - continuous conversation with progressive capability unlocking
- All logic in YAML configs, not Python code

**If you need to:**
- Add a new action → Edit action_graph.yaml
- Add a new prerequisite type → Edit action_graph.yaml prerequisite_types
- Add a new workflow moment → Edit lifecycle_events.yaml
- Change when something unlocks → Edit prerequisite conditions in YAML files

For implementation details, see:
- app/config/action_registry.py
- app/services/wu_wei_prerequisites.py
- config/workflows/action_graph.yaml
- config/workflows/lifecycle_events.yaml
"""

# This file intentionally left empty - all logic moved to config files
