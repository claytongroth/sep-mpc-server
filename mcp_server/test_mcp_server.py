#!/usr/bin/env python3
"""
Test script for the Philosophy MCP Server
Validates setup and tests basic functionality
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_vector_database():
    """Test if the vector database is accessible."""
    print("🔍 Testing vector database...")
    
    try:
        from mcp_vector_interface import PhilosophyVectorDB
        
        # Initialize database
        db = PhilosophyVectorDB()
        print("  ✅ Vector database initialized successfully")
        
        # Test basic query
        results = db.search("consciousness", n_results=3)
        print(f"  ✅ Search test successful: found {len(results['results'])} results")
        
        # Test stats
        stats = db.get_stats()
        print(f"  ✅ Database contains {stats['total_entries']} entries with {stats['total_chunks']} chunks")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Vector database error: {e}")
        return False

async def test_mcp_server():
    """Test if the MCP server can start."""
    print("\n🔧 Testing MCP server...")
    
    try:
        import philosophy_mcp_server
        print("  ✅ MCP server module imported successfully")
        
        # Test that the main components exist
        if hasattr(philosophy_mcp_server, 'main'):
            print("  ✅ Main function exists")
        
        if hasattr(philosophy_mcp_server, 'handle_list_tools'):
            print("  ✅ Tool handlers defined")
            
        if hasattr(philosophy_mcp_server, 'handle_call_tool'):
            print("  ✅ Call tool handler defined")
        
        print("  ✅ MCP server appears to be properly structured")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MCP server error: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are installed."""
    print("📦 Testing dependencies...")
    
    required_packages = [
        ('mcp', 'mcp'),
        ('sentence-transformers', 'sentence_transformers'), 
        ('chromadb', 'chromadb'),
        ('beautifulsoup4', 'bs4'),  # beautifulsoup4 imports as bs4
        ('numpy', 'numpy')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} - NOT INSTALLED")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def test_file_structure():
    """Test if required files and directories exist."""
    print("\n📁 Testing file structure...")
    
    required_paths = [
        "./vectorization/philosophy_vectordb",
        "./mcp_vector_interface.py",
        "./philosophy_mcp_server.py"
    ]
    
    all_exist = True
    
    for path in required_paths:
        if Path(path).exists():
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path} - NOT FOUND")
            all_exist = False
    
    # Check for HTML files
    html_dir = Path("./philosophy_entries")
    if html_dir.exists():
        html_files = list(html_dir.glob("*.html"))
        print(f"  ✅ {html_dir} ({len(html_files)} HTML files)")
    else:
        print(f"  ⚠️  {html_dir} - NOT FOUND (optional if vector DB already created)")
    
    return all_exist

def check_claude_config():
    """Check if Claude Desktop config exists and guide user."""
    print("\n🔧 Claude Desktop Configuration:")
    
    # Common config paths
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    elif system == "Windows":
        config_path = Path(os.environ.get('APPDATA', '')) / "Claude/claude_desktop_config.json"
    else:  # Linux
        config_path = Path.home() / ".config/claude/claude_desktop_config.json"
    
    print(f"  Expected config location: {config_path}")
    
    if config_path.exists():
        print("  ✅ Claude config file exists")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if 'mcpServers' in config and 'philosophy' in config['mcpServers']:
                print("  ✅ Philosophy server configured")
            else:
                print("  ⚠️  Philosophy server not configured in Claude")
                
        except Exception as e:
            print(f"  ⚠️  Error reading config: {e}")
    else:
        print("  ❌ Claude config file not found")
    
    # Generate sample config
    current_dir = Path.cwd().absolute()
    server_path = current_dir / "philosophy_mcp_server.py"
    
    sample_config = {
        "mcpServers": {
            "philosophy": {
                "command": "python",
                "args": [str(server_path)],
                "env": {
                    "PYTHONPATH": str(current_dir)
                }
            }
        }
    }
    
    print(f"\n📝 Sample configuration for {config_path}:")
    print(json.dumps(sample_config, indent=2))

async def main():
    """Run all tests."""
    print("🧪 Philosophy MCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("File Structure", test_file_structure),
        ("Vector Database", test_vector_database),
        ("MCP Server", test_mcp_server)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))
    
    # Configuration check (doesn't affect pass/fail)
    check_claude_config()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Results:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Your MCP server should work with Claude.")
        print("\nNext steps:")
        print("1. Update your Claude Desktop config (see sample above)")
        print("2. Restart Claude Desktop")
        print("3. Look for Philosophy tools in Claude's interface")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before using with Claude.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)