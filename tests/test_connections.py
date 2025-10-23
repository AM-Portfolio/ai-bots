#!/usr/bin/env python3
"""
Connection Test Script
Run this script to test all service connections
"""
import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.tests.test_all import test_all_connections, test_service_connection, test_runner


def main():
    """Main entry point for connection testing"""
    if len(sys.argv) == 1:
        print("AI Bots Connection Test Suite")
        print("=" * 40)
        print("Usage:")
        print("  python test_connections.py                    # Test all services")
        print("  python test_connections.py <service>          # Test specific service")
        print("  python test_connections.py list               # List available services")
        print()
        print("Available services:")
        for service in test_runner.test_functions.keys():
            print(f"  - {service}")
        print()
        print("Starting full connection test...")
        asyncio.run(test_all_connections(save=True))
    
    elif sys.argv[1].lower() == "list":
        print("Available services:")
        for service in test_runner.test_functions.keys():
            print(f"  - {service}")
    
    elif sys.argv[1].lower() == "all":
        print("Testing all service connections...")
        asyncio.run(test_all_connections(save=True))
    
    else:
        service = sys.argv[1].lower()
        if service in test_runner.test_functions:
            print(f"Testing {service} connections...")
            asyncio.run(test_service_connection(service))
        else:
            print(f"Unknown service: {service}")
            print(f"Available services: {', '.join(test_runner.test_functions.keys())}")


if __name__ == "__main__":
    main()