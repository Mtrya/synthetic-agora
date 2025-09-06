# Synthetic Agora

## Overall Architecture

The framework consists of modular layers with clear separation of concerns:

```docs
platform/ → Foundation layer (data model + operations + algorithms) ✅ COMPLETE
runtime/ → Tool execution layer (agent-tool-platform bridge) ✅ COMPLETE  
agents/ → Template layer (static definitions, personalities) 🚧 PLANNED
analysis/ → Monitoring layer (metrics, visualization) 🚧 PLANNED
```

**Critical Separation**: `agents/` defines static templates (DNA), `runtime/` manages dynamic execution (instances).

## Current File Structure

```files
synthetic-agora/
├── agora/
│   ├── __init__.py
│   ├── main.py                    # Main simulation runner (EMPTY)
│   ├── cli.py                     # Command-line interface (EMPTY)
│   ├── platform/                  # ✅ COMPLETE
│   │   ├── __init__.py             # Clean API exposure
│   │   ├── models.py               # Database schemas (207 lines)
│   │   ├── operations.py           # Atomic CRUD operations (591 lines)
│   │   ├── services.py             # Business operations (452 lines)
│   │   ├── connection.py           # Database management (252 lines)
│   │   └── feed_algorithm.py       # Content recommendation (258 lines)
│   ├── runtime/                   # ✅ COMPLETE
│   │   ├── __init__.py
│   │   ├── tool_registry.py        # Tool definitions (309 lines)
│   │   ├── action_tracker.py       # Context resolution (224 lines)
│   │   └── tool_executor.py        # Main orchestrator (276 lines)
│   ├── agents/                    # 🚧 PLANNED
│   │   └── (empty directory)
│   └── analysis/                  # 🚧 PLANNED
│       └── (empty directory)
├── tests/
├── examples/  
├── docs/
├── pyproject.toml                 # Project dependencies
└── README.md
```

## Current Implementation Status

### 1. Platform Layer (`agora/platform/`) - ✅ COMPLETE

**Purpose**: Provides comprehensive data model, operations, and content algorithms for social media simulation.

**Implemented Features**:

- **models.py** (207 lines): Complete social media schemas with 5 core models:
  - `User`: User profiles, timestamps, soft delete
  - `Post`: Posts and comments with parent-child relationships, titles
  - `Relationship`: User-to-user relationships (follow, friend, block)
  - `Reaction`: Post reactions (like, dislike, love)
  - `Community`: User communities and groups
  - `Membership`: User-community memberships with roles

- **operations.py** (591 lines): Atomic CRUD operations:
  - User operations: `create_user()`, `get_user_by_username()`, `get_user_by_id()`
  - Post operations: `create_post()`, `get_post_by_id()`, `get_posts_by_user()`, `get_post_by_title()`
  - Relationship operations: `create_relationship()`, `get_followers()`, `get_following()`
  - Reaction operations: `create_reaction()`, `get_reaction_counts()`
  - Community operations: `create_community()`, `add_user_to_community()`
  - Soft delete support across all operations

- **services.py** (452 lines): Business-level social media functions:
  - User services: `create_user_account()`, `get_user_profile()`, `get_user_stats()`
  - Post services: `create_user_post()`, `create_comment()`, `get_post_details()`, `get_post_by_title()`
  - Social services: `follow_user()`, `unfollow_user()`, `like_post()`, `unlike_post()`
  - Content services: `get_user_feed()`, `get_trending_posts()`
  - Feed integration with sophisticated algorithm

- **feed_algorithm.py** (258 lines): Advanced content recommendation system:
  - Multi-factor relevance scoring (temporal 40%, engagement 30%, social 30%)
  - Diversity boosting to prevent feed domination
  - Social proximity calculations and mutual connection analysis
  - Sophisticated post ranking with metadata

- **connection.py** (252 lines): Database management and connection handling:
  - `DatabaseManager` class for connection lifecycle
  - `initialize_database()` for quick setup
  - Session management and cleanup

- `__init__.py`: Clean API exposing only `DatabaseManager`, `initialize_database`, and `services`

**Dependencies**: None (foundation layer)

**Status**: Fully implemented and tested (1,776 total lines)

### 2. Runtime Layer (`agora/runtime/`) - ✅ COMPLETE

**Purpose**: Bridges semantic agent tool calls with platform services through sophisticated execution and context management.

**Implemented Features**:

- **tool_registry.py** (309 lines): Comprehensive tool definition and mapping system:
  - `ToolDefinition` dataclass mapping semantic tools to platform services
  - `ToolRegistry` with 6 pre-registered social media tools
  - Dynamic tool registration and response formatting
  - Schema generation for LLM consumption
  - Support for custom tool registration

- **action_tracker.py** (224 lines): Temporal action tracking and context resolution:
  - `ActionTracker` for maintaining agent action history
  - `ActionRecord` for structured action logging
  - Context parameter resolution (post_id by title, cross-user actions)
  - Agent context management with memory decay
  - Semantic-to-database ID translation

- **tool_executor.py** (276 lines): Main orchestration engine:
  - `AgentToolExecutor` coordinating complete workflow
  - Dynamic service loading and caching
  - Graceful error handling for invalid tool calls
  - Context-aware argument building
  - Multi-step workflow: tool lookup → argument mapping → service execution → response formatting

- `__init__.py`: Clean API exposing all runtime components

**Key Capabilities**:

- Execute tool calls with semantic identifiers (e.g., `like_post(title: "Hello World")`)
- Automatic context resolution (title → post_id, username inference)
- Response formatting with meaningful messages for agents
- Support for cross-agent actions and context sharing
- Extensible tool registration system

**Dependencies**: platform/ (read/write)

**Status**: Fully implemented and tested (826 total lines)

### 3. Agents Layer (`agora/agents/`) - 🚧 PLANNED

**Purpose**: Defines static agent templates and baseline characteristics.

**Planned Features**:

- **personalities.py**: Static agent templates (political orientations, demographics)
- **belief_systems.py**: Baseline belief models and cognitive biases
- **interaction_patterns.py**: Social behavior strategies and templates

**Dependencies**: None (pure definitions, no runtime state)

**Status**: Empty directory, planning phase

### 4. Analysis Layer (`agora/analysis/`) - 🚧 PLANNED

**Purpose**: Comprehensive analysis and visualization of simulation evolution.

**Planned Features**:

- **network_metrics.py**: Social graph analysis, centrality measures
- **content_analysis.py**: Sentiment tracking, topic modeling
- **behavioral_patterns.py**: Agent interaction analysis, engagement metrics
- **visualization.py**: Real-time monitoring dashboards

**Dependencies**: platform/ (read-only for analysis)

**Status**: Empty directory, planning phase

## Technical Implementation Details

### Architecture Highlights

1. **Semantic-to-Database Bridge**: Runtime layer translates high-level agent intentions (`like_post(title: "Hello")`) to database operations (`like_post(session, "alice", 1)`)
2. **Context Awareness**: Action tracking maintains temporal context for resolving semantic identifiers to database IDs
3. **Modular Design**: Clean separation between data persistence (platform), execution logic (runtime), and agent definitions (agents)
4. **Sophisticated Feed Algorithm**: Multi-factor scoring with diversity boosting for realistic content distribution
5. **Clean APIs**: Each layer exposes only necessary components while hiding internal complexity

### Key Design Decisions

1. **SQLite First**: Simple, file-based database for easy development
2. **Soft Deletes**: Preserve data integrity while allowing deletion
3. **Tool Registry Pattern**: Extensible system for mapping agent tools to platform services
4. **Action Tracking**: Temporal context resolution for semantic identifier mapping
5. **Relative Imports**: Clean module structure without core/ layer complexity

### Development Status

- **Platform layer**: 100% complete (1,776 lines) ✅
- **Runtime layer**: 100% complete (826 lines) ✅  
- **Agents layer**: 0% complete (planning phase) 🚧
- **Analysis layer**: 0% complete (planning phase) 🚧

## Next Development Steps

1. **Implement agent templates**: Create personality and belief system frameworks in agents/
2. **Build analysis tools**: Create monitoring and visualization capabilities in analysis/
3. **Add simulation orchestrator**: Implement main simulation loop in main.py
4. **Integration testing**: Ensure all modules work together seamlessly
5. **Performance optimization**: Scale for large numbers of agents and interactions

## Important Notes

The concept of **"standard social media tools"** is central to this architecture. We aim for a single "greatest common denominator" approach rather than supporting every possible social media feature. This keeps the codebase focused and maintainable while providing essential social media simulation capabilities.

**Key Innovation**: The runtime layer's ability to bridge semantic agent calls with database operations through context-aware execution enables sophisticated agent-platform interactions while maintaining clean separation of concerns.

- Put test scripts to tests/.
- Respect markdownlint specification.
