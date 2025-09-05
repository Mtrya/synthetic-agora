# Synthetic Agora

## Overall Architecture

The framework consists of five core modules with clear separation of concerns:

```docs
database/ → Foundation layer (persistent data)
executor/ → Runtime layer (agent execution, LLM coordination)
platform/ → Social physics layer (algorithms, trends, time)
agents/ → Template layer (static definitions, personalities)
analysis/ → Monitoring layer (metrics, visualization)
```

**Critical Separation**: `agents/` defines static templates (DNA), `executor/` manages dynamic runtime (instances).

## Revised File Structure

```files
synthetic-agora/
├── synthetic_agora/
│   ├── __init__.py
│   ├── main.py                    # Main simulation runner
│   ├── cli.py                     # Command-line interface
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # Database schemas and relationships
│   │   │   ├── operations.py      # Atomic CRUD operations  
│   │   │   ├── services.py        # Business level operations
│   │   │   └── connection.py      # Database connection management
│   │   ├── executor/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py    # Main simulation loop (3.1-3.5 workflow)
│   │   │   ├── tools.py           # High-level social tools with context inference
│   │   │   ├── memory.py          # Agent memory management and belief updates
│   │   │   ├── api_batch.py       # Batch API call management
│   │   │   ├── api_async.py       # Asynchronous execution handling
│   │   │   └── state_manager.py   # Agent session and LLM call state tracking
│   │   ├── platform/
│   │   │   ├── __init__.py
│   │   │   ├── feed_algorithms.py # Content recommendation and distribution
│   │   │   ├── trending.py        # Trending topic and viral content mechanics  
│   │   │   ├── moderation.py      # Content moderation and platform rules
│   │   │   └── time_stepping.py   # Simulation time progression logic
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── personalities.py   # Static agent templates (DNA)
│   │   │   ├── belief_systems.py  # Baseline belief models and cognitive biases
│   │   │   └── interaction_patterns.py # Social behavior strategies and templates
│   │   └── analysis/
│   │       ├── __init__.py
│   │       ├── network_metrics.py # Graph analysis and social network metrics
│   │       ├── content_analysis.py# Sentiment, topic, engagement analysis  
│   │       ├── behavioral_patterns.py # Agent behavior and interaction patterns
│   │       └── visualization.py   # Real-time monitoring and plotting
│   └── config.yaml                # Main configuration file
├── tests/
├── examples/  
├── docs/
└── requirements.txt
```

## Core Component Descriptions

### 1. Database (`core/database/`) - Foundation Layer

**Purpose**: Provides comprehensive social media data model with atomic operations and standard tools.

**Key Features**:

- **models.py**: Complete social media schemas (users, posts, relationships, communities, messages, reactions)  
- **operations.py**: Atomic CRUD operations (create_content, add_reaction, create_relationship, etc.)
- **services.py**: Business-level social media functions (soc.create_user_post, soc.follow_user, etc.)
- **connection.py**: Database management and connection handling

**Dependencies**: None (foundation layer)

**Implementation Priority**: Highest - All other modules depend on this

### 2. Executor (`core/executor/`) - Agent Runtime Layer

**Purpose**: Manages dynamic agent execution, LLM coordination, and high-level tool inference. The "agent runtime" that brings static templates to life.

**Key Features**:

- **orchestrator.py**: Main simulation loop implementing the Agent<->Platform interaction workflow (context preparation → LLM coordination → memory updates)
- **tools.py**: High-level social tools with context inference (`post(content)` not `post(user_id, content)`)
- **memory.py**: Agent memory management, belief updates, and context window optimization
- **api_batch.py**: Batch processing for cost-efficient API calls
- **api_async.py**: Asynchronous execution for speed optimization  
- **state_manager.py**: Agent session state and LLM call context tracking

**Dependencies**: database/ (read/write), agents/ (templates), platform/ (feed data)

**Implementation Priority**: High - Core innovation enabling LLM-database integration with context inference

### 3. Platform (`core/platform/`) - Social Media Mechanics

**Purpose**: Implements platform-level behaviors and algorithms that shape social interactions.

**Key Features**:

- **feed_algorithms.py**: Content recommendation, personalization, and distribution algorithms
- **trending.py**: Trending topic detection, viral content mechanics, zeitgeist tracking
- **moderation.py**: Content filtering, community guidelines, automated moderation
- **time_stepping.py**: Discrete round progression, event scheduling, temporal dynamics

**Dependencies**: database/ (read/write for platform operations)

**Implementation Priority**: Medium - Provides realistic platform dynamics

### 4. Agents (`core/agents/`) - Agent Template Layer

**Purpose**: Defines static agent templates and baseline characteristics. The "agent DNA" that gets instantiated by the executor.

**Key Features**:

- **personalities.py**: Static agent templates (political orientations, demographics, interests)
- **belief_systems.py**: Baseline belief models and cognitive bias templates
- **interaction_patterns.py**: Social behavior strategies and engagement templates

**Dependencies**: None (pure definitions, no runtime state)

**Implementation Priority**: Medium - Defines agent sophistication level through templates

### 5. Analysis (`core/analysis/`) - Monitoring and Research Tools

**Purpose**: Comprehensive analysis and visualization of simulation evolution.

**Key Features**:

- **network_metrics.py**: Social graph analysis, centrality measures, community detection
- **content_analysis.py**: Sentiment tracking, topic modeling, information diffusion analysis
- **behavioral_patterns.py**: Agent interaction analysis, influence networks, engagement metrics  
- **visualization.py**: Real-time monitoring dashboards, network evolution plots, opinion dynamics visualization

**Dependencies**: database/ (read-only for analysis and monitoring)

**Implementation Priority**: Medium - Essential for research utility

This architecture ensures each module can be developed and tested independently while maintaining clean dependencies through the database foundation.

## Workflow Architecture

### Main Simulation Loop (in `executor/orchestrator.py`)

Each timestep executes the 3.1-3.5 workflow:

1. **Context Preparation (3.1)**: Curate chat history and prompts
   - `platform.get_feed()` → Pure algorithm for content curation
   - `executor.memory.get_context()` → Agent-specific memory retrieval

2. **LLM Coordination (3.2-3.4)**: Tool use loop
   - `executor.api_batch.send()` → Send to LLM provider
   - `executor.tools.execute()` → Context-inferred tool execution
   - `executor.state_manager.track()` → Session state management

3. **Memory Update (3.5)**: Belief evolution
   - `executor.memory.update_beliefs()` → Dynamic belief updates
   - `executor.memory.store_interaction()` → Experience storage

### Critical Separation Principle

- **Templates vs Instances**: `agents/` creates static templates (DNA), `executor/` creates dynamic instances (runtime)
- **Context Inference**: High-level tools in `executor/tools.py` infer context (`post(content)` → `post(user_id, content)`)
- **Memory Ownership**: Agent memory is execution state → belongs in `executor/`, not `agents/`
- **Pure Algorithms**: Feed algorithms, trending, time progression → `platform/` (no agent state)

### Module Interaction Flow

```workflow
main.py
├── agents.initialize_templates()     # Static personality definitions
├── executor.initialize_agents()      # Runtime instances with memory
└── executor.run_simulation()         # Main coordination loop
    ├── platform.get_feed()           # Pure content algorithms
    ├── executor.build_context()      # Agent-specific context
    ├── executor.llm_loop()           # Tool inference & execution
    └── executor.update_memories()    # Dynamic state updates
```

### Important Notes

The concept of **"standard social media tools"**, as well as **"standard social media platforms"** and **"standard agents"** is extremely important here. Because this decides the coding style: we want a single "greatest common denominator" instead of "everything for everyone".
