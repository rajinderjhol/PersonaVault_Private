# 📋 Three-Panel Intelligence Dashboard

## 🎯 **Overview**
The Three-Panel Intelligence Dashboard provides users with full visibility and control over PersonaVault's thermodynamic memory ecosystem through an intuitive, customizable interface.

---

## 🏗️ **Architecture**

### **Left Sidebar (Collapsible + Customizable)**
- Fixed navigation items
- User-added elements (domains, widgets, bookmarks)
- Drag-to-reorder
- Persistent state (via User Preferences API)

### **Center Panel (Core Processing)**
- Chat interface with streaming responses
- Collapsible decision traces (structured reasoning pipeline)
- Memory attribution (Gas → Liquid → Ice → Snowflake)

### **Right Sidebar (Contextual + Dynamic)**
- Current decision context
- Real-time Phase metrics (WebSocket)
- Active snowflake/pattern details

---

## 🛠️ **Implementation & File Structure**

```
app/api/v1/endpoints/dashboard/templates/v2/
├── base.html              # Main layout
├── chat.html              # Chat fragment template
└── components/
    ├── context_decision.html
    └── ...                # Other context fragments

app/static/css/three_panel/
├── theme.css              # Centralized CSS variables (Dark/Light)
├── dashboard.css          # Main grid/panel layout
├── chat.css               # Chat message/input styles
└── context.css            # Right sidebar panel styles

app/static/js/three_panel/
├── dashboard.js           # Main layout controller + tab loader
├── sidebar.js             # Sidebar management (Prefs API)
├── chat_integration.js    # Chat logic/stream handler + structured response parsing
└── context.js             # WebSocket + Context panel updates
```

---

## ⚠️ **Current Issues & Troubleshooting Tracker**

| Issue | Status | Related Files | Investigation Notes |
|:---|:---|:---|:---|
| **Chat functionality** | BROKEN | `chat_integration.js`, `chat.py` | Chat returns raw blob instead of structured data; UI is unresponsive/broken. |
| **Decision Trace** | BROKEN | `context.js`, `thermodynamics.py` | Rendering `undefined` instead of pipeline data. Needs data contract audit. |
| **Sidebar Tabs** | BROKEN | `dashboard.js`, `dashboard_router.py` | Tabs fail to load expected fragments; fragments not rendering content. |
| **Styling (Inconsistent)** | BROKEN | `theme.css`, `dashboard.css` | Global theme application inconsistent across center/right panels. |

---

## 🚀 **Roadmap & Implementation Status**

### **Phase 1-5: Implementation** ❌
- [x] Layout structure & Collapsible sidebar
- [x] Sidebar Customization API & Persistent storage
- [ ] Context Panel updates via WebSocket (Failing)
- [ ] Full Chat Integration (Failing)
- [ ] Thermodynamic API observability (Inconsistent)

### **Phase 6: Refinement (CRITICAL)**
- [ ] **Data Contract Audit**: Backend/Frontend contract for `OrchestratorResult` is broken.
- [ ] **Tab System Overhaul**: Fix fragment lookup paths and rendering logic.
- [ ] **Style Coherence**: Debug theme variable inheritance.
---
