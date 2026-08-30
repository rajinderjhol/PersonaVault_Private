# PersonaVault v3: Layout Architecture - Three-Panel Studio

## 1. Left Panel (Collapsible: 240px ↔ 60px)
- **Brand + Version**: PersonaVault v3 branding.
- **Navigation**:
  - Core modules (Dashboard, Lab, Vault, Marketplace, etc.) with active states.
  - User-configurable modules (Add/Remove).
  - Workspace switcher (Personal, Organization, Team).
- **Favorites**: Quick access to saved patterns, traces, and queries.
- **Quick Actions**: "New Chat", "New Pattern", "Manual Crystallize".
- **Notifications**: System-wide alert drawer with badges.
- **Global Search**: (Cmd+K) Universal search across all memory layers and traces.
- **Status Indicators**: Real-time status for AI Providers, Memory Hit Rate, and System Health.
- **Footer**: User profile avatar, Global Settings, Theme toggle (Dark/Light), and Session logout.

## 2. Core Panel (Intelligence Engine - Flex)
- **Header**: Current module name, breadcrumbs, and context-aware primary actions.
- **Toolbar**: Module-specific toolsets and floating toolbars.
- **Content Area**:
  - Primary module interaction space (e.g., Chat flow, Pattern IDE, Graph view).
  - Support for split-views (Comparison mode) and floating utility panels.
- **Footer**: System status bar showing active Provider (e.g., Groq), Execution Mode (e.g., Sovereign), and real-time performance stats (Token/sec).

## 3. Right Panel (Contextual Intelligence - 320px)
- **Context Header**: Active entity/context name with Pin/Unpin capability.
- **Intelligence Context**:
  - **Memory Phases**: Animated visualization of Gas → Liquid → Ice state changes.
  - **Phase Transitions**: Live feed of internal thermodynamics (Freeze, Melt, Evaporate).
  - **Active Decision**: Real-time 5-step Auditable Decision Trace for the current query.
- **Pattern Context**: Related crystallized patterns, provenance metadata, and knowledge graph sub-nodes.
- **Search Context**: Dynamic search results, filters, and facets based on the current active view.
- **Quick Actions**: Context-aware buttons (Share, Export, Annotate).
- **Notifications**: Module-specific alerts and background job status.
