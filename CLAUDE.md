# Synthetic Agora

## Overall Architecture

The framework consists of five core modules, all (except database/ itself) depending on the foundational database layer:

```
database/ → {executor/, platform/, agents/, analysis/}
```

Each module (except database/) can function independently when provided with database access, enabling modular development and testing.

## Revised File Structure

```
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
│   │   │   ├── tools.py           # Standard social media tools (post, like, follow, etc.)
│   │   │   └── connection.py      # Database connection management
│   │   ├── executor/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py    # Core LLM+DB coordination logic
│   │   │   ├── api_batch.py       # Batch API call management
│   │   │   ├── api_async.py       # Asynchronous execution handling
│   │   │   └── state_manager.py   # Agent session and call state tracking
│   │   ├── platform/
│   │   │   ├── __init__.py
│   │   │   ├── feed_algorithms.py # Content recommendation and distribution
│   │   │   ├── trending.py        # Trending topic and viral content mechanics  
│   │   │   ├── moderation.py      # Content moderation and platform rules
│   │   │   └── time_stepping.py   # Simulation time progression logic
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── personalities.py   # Standard agent personality templates
│   │   │   ├── memory.py          # Agent memory management and retrieval
│   │   │   ├── belief_systems.py  # Belief evolution and opinion dynamics
│   │   │   └── interaction_patterns.py # Social interaction strategies
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

### 2. Executor (`core/executor/`) - API Orchestration Layer  

**Purpose**: Standalone orchestrator that bridges LLM API calls with database operations, acting as a pure coordination mixin.

**Key Features**:
- **orchestrator.py**: Core logic for coordinating LLM function calling with database tool execution
- **api_batch.py**: Batch processing for cost-efficient API calls
- **api_async.py**: Asynchronous execution for speed optimization  
- **state_manager.py**: Tracks agent session state and API call context (read-only database access, temporary write blocking)

**Dependencies**: database/ (read-only during execution, coordination of writes)

**Implementation Priority**: High - Core innovation enabling LLM-database integration

### 3. Platform (`core/platform/`) - Social Media Mechanics

**Purpose**: Implements platform-level behaviors and algorithms that shape social interactions.

**Key Features**:
- **feed_algorithms.py**: Content recommendation, personalization, and distribution algorithms
- **trending.py**: Trending topic detection, viral content mechanics, zeitgeist tracking
- **moderation.py**: Content filtering, community guidelines, automated moderation
- **time_stepping.py**: Discrete round progression, event scheduling, temporal dynamics

**Dependencies**: database/ (read/write for platform operations)

**Implementation Priority**: Medium - Provides realistic platform dynamics

### 4. Agents (`core/agents/`) - Agent Behavior Systems

**Purpose**: Defines agent personalities, memory systems, and interaction patterns.

**Key Features**:
- **personalities.py**: Standard agent templates (political orientations, demographics, interests)
- **memory.py**: Long-term memory management, experience retrieval, context window optimization  
- **belief_systems.py**: Opinion formation models, belief updating mechanisms, cognitive biases
- **interaction_patterns.py**: Social behavior strategies, engagement patterns, relationship formation

**Dependencies**: database/ (agent state storage and retrieval - needs clarification on interaction pattern)

**Implementation Priority**: Medium - Defines agent sophistication level

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

### Important Notes
The concept of **"standard social media tools"**, as well as **"standard social media platforms"** and **"standard agents"** is extremely important here. Because this decides the coding style: we want a single "greatest common denominator" instead of "everything for everyone".
