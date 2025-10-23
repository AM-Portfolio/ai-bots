"""Master test runner for all service connections"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any

# Import all test modules
from .test_azure import test_all_azure_services
from .test_together import test_all_together_services
from .test_github import test_all_github_services
from .test_confluence import test_all_confluence_services
from .test_jira import test_all_jira_services
from .test_vector import test_all_vector_services

logger = logging.getLogger(__name__)


class ConnectionTestRunner:
    """Master test runner for all service connections"""
    
    def __init__(self):
        self.test_functions = {
            "azure": test_all_azure_services,
            "together": test_all_together_services,
            "github": test_all_github_services,
            "confluence": test_all_confluence_services,
            "jira": test_all_jira_services,
            "vector": test_all_vector_services
        }
    
    async def test_all_services(self, services: list = None) -> Dict[str, Any]:
        """Test all or specific services"""
        if services is None:
            services = list(self.test_functions.keys())
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "services_tested": services,
            "results": {},
            "overall_summary": {}
        }
        
        logger.info(f"Starting connection tests for services: {', '.join(services)}")
        
        # Run tests for each service
        for service_name in services:
            if service_name not in self.test_functions:
                logger.warning(f"Unknown service: {service_name}")
                continue
            
            logger.info(f"Testing {service_name}...")
            try:
                test_function = self.test_functions[service_name]
                service_results = await test_function()
                results["results"][service_name] = service_results
                logger.info(f"Completed testing {service_name}")
            except Exception as e:
                logger.error(f"Error testing {service_name}: {e}")
                results["results"][service_name] = {
                    "error": f"Test execution failed: {e}",
                    "summary": {
                        "total_services": 0,
                        "configured_services": 0,
                        "connected_services": 0,
                        "success_rate": "0/0"
                    }
                }
        
        # Calculate overall summary
        total_services = 0
        total_configured = 0
        total_connected = 0
        
        for service_name, service_results in results["results"].items():
            if "summary" in service_results:
                summary = service_results["summary"]
                total_services += summary.get("total_services", 0)
                total_configured += summary.get("configured_services", 0)
                total_connected += summary.get("connected_services", 0)
        
        results["overall_summary"] = {
            "total_services": total_services,
            "configured_services": total_configured,
            "connected_services": total_connected,
            "success_rate": f"{total_connected}/{total_configured}" if total_configured > 0 else "0/0",
            "service_categories": len(services),
            "healthy_categories": sum(1 for r in results["results"].values() 
                                    if "summary" in r and r["summary"].get("connected_services", 0) > 0)
        }
        
        logger.info(f"Connection tests completed: {results['overall_summary']['success_rate']} services connected")
        
        return results
    
    async def test_service(self, service_name: str) -> Dict[str, Any]:
        """Test a specific service"""
        return await self.test_all_services([service_name])
    
    def print_results(self, results: Dict[str, Any], detailed: bool = True):
        """Print test results in a formatted way"""
        print(f"\n{'='*60}")
        print(f"CONNECTION TEST RESULTS - {results['timestamp']}")
        print(f"{'='*60}")
        
        # Overall summary
        summary = results["overall_summary"]
        print(f"\nOVERALL SUMMARY:")
        print(f"  Service categories tested: {summary['service_categories']}")
        print(f"  Healthy categories: {summary['healthy_categories']}")
        print(f"  Total services: {summary['total_services']}")
        print(f"  Configured services: {summary['configured_services']}")
        print(f"  Connected services: {summary['connected_services']}")
        print(f"  Success rate: {summary['success_rate']}")
        
        # Individual service results
        for service_category, service_results in results["results"].items():
            print(f"\n{'-'*40}")
            print(f"{service_category.upper()} SERVICES")
            print(f"{'-'*40}")
            
            if "error" in service_results:
                print(f"  ERROR: {service_results['error']}")
                continue
            
            if "summary" in service_results:
                svc_summary = service_results["summary"]
                print(f"  Configured: {svc_summary['configured_services']}/{svc_summary['total_services']}")
                print(f"  Connected: {svc_summary['connected_services']}/{svc_summary['configured_services']}")
                print(f"  Success rate: {svc_summary['success_rate']}")
            
            if detailed:
                for test_name, test_result in service_results.items():
                    if test_name == "summary":
                        continue
                    
                    print(f"\n  {test_result.get('service', test_name)}:")
                    print(f"    Configured: {test_result.get('configured', False)}")
                    print(f"    Connected: {test_result.get('connection', False)}")
                    
                    if test_result.get('error'):
                        print(f"    Error: {test_result['error']}")
                    
                    if detailed and test_result.get('details'):
                        print(f"    Details: {test_result['details']}")
        
        print(f"\n{'='*60}")
    
    async def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"connection_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None


# Convenience instance
test_runner = ConnectionTestRunner()


async def test_all_connections(detailed: bool = True, save: bool = False) -> Dict[str, Any]:
    """Test all service connections and print results"""
    results = await test_runner.test_all_services()
    test_runner.print_results(results, detailed=detailed)
    
    if save:
        filename = await test_runner.save_results(results)
        if filename:
            print(f"\nResults saved to: {filename}")
    
    return results


async def test_service_connection(service: str, detailed: bool = True) -> Dict[str, Any]:
    """Test a specific service connection"""
    results = await test_runner.test_service(service)
    test_runner.print_results(results, detailed=detailed)
    return results


if __name__ == "__main__":
    async def main():
        import sys
        
        if len(sys.argv) > 1:
            service = sys.argv[1].lower()
            if service in test_runner.test_functions:
                print(f"Testing {service} connections...")
                await test_service_connection(service)
            else:
                print(f"Unknown service: {service}")
                print(f"Available services: {', '.join(test_runner.test_functions.keys())}")
        else:
            print("Testing all connections...")
            await test_all_connections(save=True)
    
    asyncio.run(main())