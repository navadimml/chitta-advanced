# Chitta Documentation Index

**Last Updated**: November 2, 2025 (Interview Implementation Added)

This guide helps you navigate all documentation files and understand what each one covers.

---

## 📚 Essential Documentation (Read These)

### 1. **ARCHITECTURE_V2.md** ⭐
**Start Here for Technical Understanding**

- Complete system architecture
- Domain-agnostic design principles
- How to adapt to any use case
- Component catalog with code examples
- State management patterns
- API integration guide
- Production migration path

**Best For**: Developers building or adapting the app

---

### 2. **UI_UX_STYLE_GUIDE.md** ⭐
**Start Here for Design Understanding**

- Complete visual design system
- Color palette and typography
- All animations and timing
- Micro-interactions catalog
- Component patterns with code
- Accessibility guidelines
- Responsive design patterns
- Creating "magical" experiences

**Best For**: Designers, frontend developers, UX teams

---

### 3. **GRAPHITI_INTEGRATION_GUIDE.md** ⭐
**Start Here for Backend Integration**

- AI model abstraction (Claude, GPT-4, etc.)
- Graph database flexibility (Neo4j vs FalkorDB)
- Temporal knowledge graph architecture
- Episode-based data ingestion
- Context-aware consultation patterns
- Performance comparisons
- Production deployment guide

**Best For**: Backend developers, data architects

---

### 4. **CORE_INNOVATION_DETAILED.md**
**Start Here for Philosophy**

- The fundamental problem we solve
- Why chat interfaces fail at random access
- Two-layer system (Conversation + Context Surface)
- Proactive re-orientation
- Smart routing between journeys
- Design philosophy deep dive

**Best For**: Product managers, UX researchers, stakeholders

---

## 🛠️ Implementation Documentation

### 5. **ARCHITECTURE_ALIGNMENT_ANALYSIS.md**
**Code vs Documentation Alignment**

- Compares existing code with documented principles
- Identifies conflicts and gaps
- Alignment scoring by layer
- Migration recommendations

**Best For**: Developers refactoring existing code
**Key Insight**: Visual layer 100% aligned, core architecture 51% aligned

---

### 6. **ARCHITECTURE_RECONCILIATION.md** ⭐
**Resolving Conversation-First vs Technical Dependencies**

- Core insight: "Conversation-first interface over prerequisite graph"
- Intent-based routing with graceful prerequisite handling
- Backend dependency management (invisible to user)
- LLM-based feasibility checking

**Best For**: Architects, developers implementing screening workflows
**Key Pattern**: Backend maintains dependency graph, LLM explains gracefully when blocked

---

### 7. **IMPLEMENTATION_DEEP_DIVE.md** ⭐
**Technical Implementation Specifications**

- Message processing flow with LLM function calling
- Continuous extraction paradigm
- Interview summary mechanism
- Question filtering and handling
- Context card generation logic
- Single-agent architecture with function calling

**Best For**: Backend developers implementing conversation engine
**Key Functions**: `extract_interview_data`, `user_wants_action`, `user_is_stuck`

---

### 8. **INTERVIEW_SYSTEM_PROMPT_REFACTORED.md** ⭐
**Interview Conductor LLM Prompt**

- Complete system prompt for interview agent
- Function calling integration
- Continuous extraction guidelines
- Handling questions mid-interview
- Warm, empathetic Hebrew conversation patterns
- Completeness-based progression

**Best For**: Prompt engineers, LLM integration developers
**Key Change**: Removed JSON output and stage gates, added continuous extraction

---

### 9. **INTERVIEW_IMPLEMENTATION_GUIDE.md** ⭐
**Interview Backend Implementation**

- Function definitions for LLM
- Message processing flow code
- Function call handlers
- Completeness calculation algorithm
- Frontend integration patterns
- Testing strategies

**Best For**: Backend developers implementing interview system
**Code Examples**: Complete Python implementation with Graphiti

---

### 10. **VIDEO_ANALYSIS_SYSTEM_PROMPT.md** ⭐
**Video Analysis System Prompt**

- Complete Gemini prompt for video analysis
- DSM-5 observational framework
- Integration with interview summary data
- Timestamp-based evidence justification
- Non-diagnostic observational stance
- Example analysis output with Hebrew

**Best For**: Prompt engineers, clinical developers
**Key Feature**: Analyzes videos while integrating parent interview data for comprehensive screening

---

## 📖 Reference Documentation

### 11. **README.md**
- Quick start guide
- Project structure
- Available scenarios
- Running the app locally
- Current implementation status

---

### 11. **ARCHITECTURE.md** (Legacy)
- Original architecture document
- Still accurate for core patterns
- Superseded by ARCHITECTURE_V2.md for completeness

**Note**: Use ARCHITECTURE_V2.md for new projects

---

### 12. **IMPLEMENTATION_STATUS.md**
- Component completion checklist
- All 17 components marked complete
- Feature implementation tracking

---

### 13. **COMPLETE.md**
- Final completion summary
- Statistics and metrics
- What's been delivered

---

## 🗂️ Legacy/Historical Documentation

These documents capture the evolution of our thinking. They contain valuable insights but have been superseded by the v2 documentation.

### 14. **AI_AGENT_IMPLEMENTATION_GUIDE.md**
- Initial AI agent architecture (2,244 lines)
- Some patterns superseded by GRAPHITI_INTEGRATION_GUIDE.md
- Historical value: Shows original Zustand-based approach
- **Replaced by**: GRAPHITI_INTEGRATION_GUIDE.md (newer, better)

---

### 15. **AI_AGENT_INTEGRATION_ALIGNED.md**
- Corrected integration aligned with Chitta philosophy
- Important clarifications on UI/UX patterns
- **Incorporated into**: ARCHITECTURE_V2.md and UI_UX_STYLE_GUIDE.md

---

## 🎯 Quick Navigation by Role

### I'm a **Developer** new to the project
1. Read: **ARCHITECTURE_V2.md** (architecture)
2. Skim: **UI_UX_STYLE_GUIDE.md** (visual patterns)
3. Reference: **README.md** (getting started)

### I'm a **Designer** joining the team
1. Read: **UI_UX_STYLE_GUIDE.md** (design system)
2. Read: **CORE_INNOVATION_DETAILED.md** (philosophy)
3. Reference: **ARCHITECTURE_V2.md** (component catalog)

### I'm a **Backend Developer**
1. Read: **GRAPHITI_INTEGRATION_GUIDE.md** (data layer)
2. Read: **IMPLEMENTATION_DEEP_DIVE.md** (conversation engine)
3. Read: **INTERVIEW_IMPLEMENTATION_GUIDE.md** (interview system)
4. Reference: **ARCHITECTURE_V2.md** (API patterns)
5. Reference: **INTERVIEW_SYSTEM_PROMPT_REFACTORED.md** (LLM prompt)

### I'm a **Product Manager**
1. Read: **CORE_INNOVATION_DETAILED.md** (what problem we solve)
2. Read: **UI_UX_STYLE_GUIDE.md** (user experience)
3. Reference: **ARCHITECTURE_V2.md** (technical feasibility)

### I want to **Adapt to Another Domain**
1. Read: **ARCHITECTURE_V2.md** → "Domain-Agnostic Architecture" section
2. Read: **UI_UX_STYLE_GUIDE.md** → "Customization Guide" section
3. Reference: **GRAPHITI_INTEGRATION_GUIDE.md** for backend

---

## 📋 Documentation Comparison

| Document | Lines | Focus | Audience | Status |
|----------|-------|-------|----------|--------|
| ARCHITECTURE_V2.md | ~1,100 | Technical architecture | Developers | ⭐ Current |
| UI_UX_STYLE_GUIDE.md | ~1,400 | Design system | Designers/Devs | ⭐ Current |
| GRAPHITI_INTEGRATION_GUIDE.md | ~1,650 | Backend/Data + Gemini | Backend devs | ⭐ Current |
| ARCHITECTURE_RECONCILIATION.md | ~500 | Conversation-first + deps | Architects | ⭐ Current |
| IMPLEMENTATION_DEEP_DIVE.md | ~700 | Technical specs | Backend devs | ⭐ Current |
| INTERVIEW_SYSTEM_PROMPT_REFACTORED.md | ~370 | Interview prompt | Prompt engineers | ⭐ Current |
| INTERVIEW_IMPLEMENTATION_GUIDE.md | ~650 | Interview backend | Backend devs | ⭐ Current |
| VIDEO_ANALYSIS_SYSTEM_PROMPT.md | ~850 | Video analysis prompt | Prompt/Clinical devs | ⭐ Current |
| ARCHITECTURE_ALIGNMENT_ANALYSIS.md | ~400 | Code vs docs | Refactoring | Current |
| CORE_INNOVATION_DETAILED.md | ~700 | Philosophy | Product/UX | Current |
| AI_AGENT_IMPLEMENTATION_GUIDE.md | 2,244 | Initial AI design | Historical | Legacy |
| AI_AGENT_INTEGRATION_ALIGNED.md | 855 | Aligned design | Historical | Legacy |
| ARCHITECTURE.md | ~400 | Original arch | Reference | Legacy |
| README.md | ~200 | Getting started | All | Current |
| IMPLEMENTATION_STATUS.md | ~150 | Progress tracking | All | Current |

---

## 🎓 Learning Path

### Week 1: Understand the Vision
- Day 1-2: **CORE_INNOVATION_DETAILED.md** + **README.md**
- Day 3-4: **UI_UX_STYLE_GUIDE.md** (first half)
- Day 5: **ARCHITECTURE_V2.md** (overview sections)

### Week 2: Deep Dive
- Day 1-3: **ARCHITECTURE_V2.md** (all sections)
- Day 4-5: **UI_UX_STYLE_GUIDE.md** (complete)

### Week 3: Backend & Integration
- Day 1-2: **GRAPHITI_INTEGRATION_GUIDE.md**
- Day 3: **ARCHITECTURE_RECONCILIATION.md**
- Day 4-5: **IMPLEMENTATION_DEEP_DIVE.md**
- Practice: Set up local environment, explore code

### Week 4: Interview System Implementation
- Day 1: **INTERVIEW_SYSTEM_PROMPT_REFACTORED.md** (understand the prompt)
- Day 2-3: **INTERVIEW_IMPLEMENTATION_GUIDE.md** (build backend)
- Day 4-5: Test and refine interview flow
- Practice: Implement continuous extraction, test with real LLM

### Week 5: Build Something
- Adapt a component to new domain
- Implement a new deep view
- Create custom scenario

---

## 🔄 Documentation Maintenance

### When to Update Each Doc

**ARCHITECTURE_V2.md**:
- New component added
- Major architectural change
- New pattern discovered

**UI_UX_STYLE_GUIDE.md**:
- New animation added
- Color palette change
- New micro-interaction
- Accessibility improvement

**GRAPHITI_INTEGRATION_GUIDE.md**:
- New database support
- LLM provider added
- Query pattern optimization

**IMPLEMENTATION_DEEP_DIVE.md**:
- New LLM function added
- Message processing flow changes
- Context card generation logic updates

**INTERVIEW_SYSTEM_PROMPT_REFACTORED.md**:
- Interview conversation patterns change
- New extraction fields added
- Hebrew language refinements

**INTERVIEW_IMPLEMENTATION_GUIDE.md**:
- Function handler implementation changes
- Completeness calculation algorithm updates
- New testing patterns

**ARCHITECTURE_RECONCILIATION.md**:
- New prerequisite dependencies added
- Intent routing patterns change
- Graceful blocking scenarios discovered

**CORE_INNOVATION_DETAILED.md**:
- Philosophy evolution
- New insights from user research
- Fundamental pattern changes

---

## ❓ FAQ

### Q: Which doc should I read first?
**A**: Depends on your role. See "Quick Navigation by Role" above.

### Q: Are the legacy docs still useful?
**A**: Yes, for historical context. They show the evolution of thinking. But for implementation, use v2 docs.

### Q: Can I delete the legacy docs?
**A**: Not recommended. They contain valuable context for design decisions. Mark them clearly as "Legacy" instead.

### Q: The docs seem long. Do I need to read everything?
**A**: No! Each doc is modular. Read sections relevant to your current task.

### Q: How do I know if docs are up to date?
**A**: Check "Last Updated" date at top of each file. Files marked ⭐ are actively maintained.

---

## 🎯 Document Purpose Summary

```
ARCHITECTURE_V2.md ──────────────────────► Technical "How"
UI_UX_STYLE_GUIDE.md ────────────────────► Visual "How"
GRAPHITI_INTEGRATION_GUIDE.md ───────────► Backend "How" + Gemini Integration
CORE_INNOVATION_DETAILED.md ─────────────► Philosophical "Why"

ARCHITECTURE_RECONCILIATION.md ──────────► Conversation + Dependencies
IMPLEMENTATION_DEEP_DIVE.md ─────────────► Technical Specs
INTERVIEW_SYSTEM_PROMPT_REFACTORED.md ───► Interview LLM Prompt
INTERVIEW_IMPLEMENTATION_GUIDE.md ───────► Interview Backend Code
VIDEO_ANALYSIS_SYSTEM_PROMPT.md ─────────► Video Analysis LLM Prompt (DSM-5)
ARCHITECTURE_ALIGNMENT_ANALYSIS.md ──────► Code vs Docs Gap Analysis

README.md ───────────────────────────────► Quick Start
IMPLEMENTATION_STATUS.md ────────────────► Progress Tracking
COMPLETE.md ─────────────────────────────► Summary Statistics

Legacy docs ─────────────────────────────► Historical context
```

**Complete Workflow**: Interview Prompt → Interview Code → Video Prompt → Backend Integration → Reports

---

## 📞 Getting Help

**Can't find what you're looking for?**

1. Check this index first
2. Use your editor's search (Cmd/Ctrl + Shift + F)
3. Search for specific component names or patterns
4. Review code in `/src/components/` directly

**Found an error in docs?**

1. Note the file name and section
2. Submit correction with clear description
3. Update "Last Updated" date when fixing

---

**This documentation system is designed to be comprehensive yet navigable. Start with the ⭐ starred docs relevant to your role.**
