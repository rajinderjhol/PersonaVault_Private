# PersonaVault v3: Sovereign Decision Studio - Frontend Design Document

## 1. Objective
To build a state-of-the-art, future-proof frontend for PersonaVault that transcends basic chat interfaces. This "Sovereign Decision Studio" will visualize the system's cognitive intelligence, memory thermodynamics, and auditable decision processes. This document serves as the authoritative engineering guide for implementation.

## 2. Project Location
The new frontend will be initialized in the following directory to ensure clean separation from backend services:
- **Root Directory:** `/home/rajinderj8888/personavault/backend/studio`

## 3. Architecture & Tech Stack
- **Framework:** React 18+ (TypeScript)
- **Build Tool:** Vite
- **Styling:** Vanilla CSS (CSS Modules) with CSS Variables for theme management.
- **Aesthetic:** "Cyber-Industrial" / Glassmorphism. Dark mode primary.
  - **Gas (Working):** `#00f2ff` (Neon Cyan)
  - **Liquid (Episodic):** `#3b82f6` (Royal Blue)
  - **Ice (Semantic):** `#f8fafc` (Crystal White)
- **State Management:** Zustand (global UI/Auth), React Query (server state/caching).
- **Animations:** Framer Motion (Phase transitions, panel animations).
- **Visualizations:** D3.js or React Flow (Decision Traces, Memory Graphs).
- **Icons:** Lucide React.

## 4. Layout Architecture: Three-Panel Sovereign Studio

### 4.1 Left Panel (Collapsible: 240px ↔ 60px)
- **Brand + Version**: PersonaVault v3 branding.
- **Navigation**: Core modules, User modules, Workspace switcher.
- **Favorites, Quick Actions, Notifications, Global Search (Cmd+K).**
- **Status Indicators & Footer (Profile, Settings, Theme toggle).**

### 4.2 Core Panel (Intelligence Engine - Flex)
- **Header, Toolbar, Content Area (Split-views, Floating panels).**
- **Footer**: System status bar (Provider, Execution Mode, Performance stats).

### 4.3 Right Panel (Contextual Intelligence - 320px)
- **Context Header, Intelligence Context (Phases & ADT Trace), Pattern Context, Search Context.**
- **Quick Actions & Notifications (Context-aware).**

## 5. Code Structure: Modular Sovereign Studio

```text
studio/src/
├── api/                          # API Layer (Axios/Fetch + WebSocket handlers)
│   ├── endpoints/                # chat, traces, thermodynamics, mcp, etc.
│   └── websocket/                # connection client and message routers
├── components/                   # UI Components
│   ├── layout/                   # Three-Panel (Left/Core/Right) wrappers
│   ├── modules/                  # Feature-specific modules (Lab, Vault, etc.)
│   ├── common/                   # Reusable UI (Button, Card, Modal)
│   └── visualizations/           # D3/React Flow logic (DecisionGraph, MemoryDiagram)
├── hooks/                        # Custom React Hooks (useAuth, useTraces, useMCP)
├── store/                        # State Management (Zustand)
│   ├── uiStore.ts                # UI state (theme, panels)
│   ├── chatStore.ts              # Chat sessions
│   └── thermodynamicsStore.ts    # Memory phases
├── styles/                       # CSS Variables, Glassmorphism, Animations
├── types/                        # TypeScript Types (api, chat, traces, etc.)
├── utils/                        # Formatters, Helpers, Constants
└── routes/                       # React Router setup and Guards
```

### Module Independence Principle
Each module (e.g., `CognitiveLab`) is self-contained with its own components, hooks, and types, allowing for lazy-loading and independent testing.

## 6. Strategic Value: The Leap-Frog Advantage

### 6.1 What Makes This Leap-Frog
- **Sovereign by Design**: User owns their intelligence.
- **Thermodynamic Memory**: Self-optimizing intelligence layers (Gas/Liquid/Ice/Snowflakes).
- **10,000:1 Compression**: Massive efficiency through crystallized patterns.
- **MCP Native**: Ubiquitous integration via Model Context Protocol.
- **Decision Replay**: Full scrubbability via Auditable Decision Traces (ADT).

### 6.2 What This Enables
- **Institutional Intelligence**: Accumulate durable organizational knowledge.
- **Compounding Returns**: Every interaction makes the system smarter.
- **Trust**: Verifiable evidence → action lineage for every AI decision.

## 7. Core Modules
- **1. Command Center**: Intelligence Pulse and Swarm metrics.
- **2. Cognitive Lab**: Chat, Thought Narrative, and Trace Replay.
- **3. Intelligence Vault**: Thermodynamics, Crystallization Dashboard, Snowflakes.
- **4. MCP Command Center**: Server/Client IDE and Tool Metrics.
- **5. Device Trust Center**: Trust Map and Edge Sync status.
- **6. Pattern Compiler Studio**: Behavior Pack IDE and Compiler Hub.
- **7. Governance & Compliance**: Constitutional Editor and VeriLink Integration.
- **8. Sovereign Control Center**: Execution Guards and Air-Gapped controls.
- **9. Developer Console**: API Explorer and WebSocket Monitor.

## 8. Detailed Implementation Breakdown

### Phase 1: Foundation & Layout Architecture
- [ ] **Studio Initialization**: Initialize Vite + React + TypeScript in the `studio/` folder.
- [ ] **State & Store Setup**: Configure Zustand stores for `uiStore` (panels/themes) and `authStore`.
- [ ] **Three-Panel Layout**: Implement the `AppLayout` component using CSS Grid/Flex to manage the 240px Sidebar, Flex Core, and 320px Context Panel.
- [ ] **Theme Foundation**: Define the "Cyber-Industrial" CSS variables (Neon Cyan, Royal Blue, Crystal White).

### Phase 2: Cognitive Lab & Decision Tracing
- [ ] **Multi-modal Chat**: Build the `ChatInterface` supporting streaming text and file attachments.
- [ ] **Thought Narrative Feed**: Implement the real-time agent reasoning stream in the Core Panel.
- [ ] **ADT Decision Graph**: Develop the D3.js/React Flow visualization for the 5-step trace in the Right Panel.
- [ ] **Historical Replay**: Integrate the scrubbable timeline for historical trace navigation.

### Phase 3: Thermodynamic Memory & Vault
- [ ] **Thermodynamic View**: Build the visual representation of memory layers (Gas/Liquid/Ice).
- [ ] **Crystallization Dashboard**: Visualize the 10,000:1 compression metrics and reinforcement history.
- [ ] **Phase Controls**: Implement the manual Freeze/Melt/Evaporate UI triggers.
- [ ] **Snowflake Manager**: UI for creating and managing domain-specific variants.

### Phase 4: MCP Ecosystem & Sovereign Security
- [ ] **MCP Command Center**: Build the server/client management IDE and tool metrics dashboard.
- [ ] **Device Trust Map**: Implement the visual device graph with trust score indicators.
- [ ] **Sovereign Execution Guards**: Develop the toggle interface for Restricted, Simulation, and Audit modes.

### Phase 5: Pattern Compiler & Developer Studio
- [ ] **Behavior Pack IDE**: Create the visual editor for `pack.yaml` behavior logic.
- [ ] **Compiler Hub**: Implement live validation and compilation status monitoring.
- [ ] **API Explorer**: Build the interactive sandbox for REST/WebSocket event testing.

### Phase 6: Integration, Polishing & Governance
- [ ] **Governance Editor**: Visual interface for `governance_constitution.json`.
- [ ] **VeriLink Integration**: Status indicators for cryptographic provenance.
- [ ] **Motion & Polish**: Apply Framer Motion transitions for Melt/Freeze effects and panel animations.
- [ ] **Performance Pass**: Optimize high-frequency WebSocket updates and trace rendering.

## 9. Verification & Testing
- **ADT Continuity**: Verify Core Panel query triggers Right Panel trace.
- **Thermodynamic Parity**: Verify UI phase transitions update backend repos.
- **Sovereign Isolation**: Verify Restricted mode disables external calls.
- **Ecosystem Test**: MCP tool invocation visibility and Device Sync accuracy.
