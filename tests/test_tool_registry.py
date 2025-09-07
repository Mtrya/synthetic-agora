#!/usr/bin/env python3
"""
Test script for the refactored tool registry.

Verifies that all 9 tools are properly mapped to the unified services.
"""

import sys
from pathlib import Path

# Add the agora directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agora.platform.connection import initialize_database
from agora.runtime.tool_registry import ToolRegistry
from agora.runtime.tool_executor import AgentToolExecutor


def test_tool_registry():
    """Test that all 9 tools are properly registered."""
    print("🧪 Testing Tool Registry Refactoring")
    print("=" * 50)
    
    # Initialize tool registry
    registry = ToolRegistry()
    tools = registry.get_all_tools()
    
    print(f"✅ Registered {len(tools)} tools:")
    
    # Expected tools
    expected_tools = [
        "create_post",
        "create_response", 
        "view_post",
        "react_to_post",
        "react_to_response",
        "connect_with_user",
        "manage_community",
        "get_discovery",
        "search"
    ]
    
    # Check all expected tools are present
    missing_tools = []
    for tool_name in expected_tools:
        if tool_name in tools:
            tool_def = tools[tool_name]
            print(f"  ✓ {tool_name} -> {tool_def.service}")
        else:
            missing_tools.append(tool_name)
    
    if missing_tools:
        print(f"❌ Missing tools: {missing_tools}")
        return False
    
    print("\n🧪 Testing Tool Executor Integration")
    print("=" * 50)
    
    # Initialize database
    test_db_path = "test_tool_registry.db"
    db = initialize_database(test_db_path)
    
    try:
        # Initialize tool executor
        executor = AgentToolExecutor(db, registry)
        available_tools = executor.get_available_tools()
        
        print(f"✅ Available tools: {len(available_tools)}")
        
        # Check service cache
        service_cache = executor._service_cache
        print(f"✅ Service cache: {list(service_cache.keys())}")
        
        # Test that all services are cached
        expected_services = [
            "agent_create_post",
            "agent_create_response",
            "agent_view_post", 
            "agent_react_to_post",
            "agent_react_to_response",
            "agent_connect_with_user",
            "agent_manage_community",
            "agent_get_discovery",
            "agent_search"
        ]
        
        missing_services = []
        for service in expected_services:
            if service not in service_cache:
                missing_services.append(service)
        
        if missing_services:
            print(f"❌ Missing services in cache: {missing_services}")
            return False
        
        print("\n🧪 Testing Tool Schema Generation")
        print("=" * 50)
        
        # Test schema generation
        schema = registry.get_tools_schema()
        print(f"✅ Generated schema for {len(schema)} tools")
        
        for tool_schema in schema:
            tool_name = tool_schema["name"]
            params = tool_schema["parameters"]["properties"]
            required = tool_schema["parameters"]["required"]
            print(f"  ✓ {tool_name}: {len(params)} params, {len(required)} required")
        
        print("\n🎉 All tests passed! Tool registry refactoring successful.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        db.close()
        Path(test_db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    success = test_tool_registry()
    sys.exit(0 if success else 1)