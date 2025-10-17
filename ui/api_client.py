import requests
from typing import Dict, Any, Optional
import os


class APIClient:
    """Client for interacting with AI Dev Agent API"""
    
    def __init__(self, base_url: str = None):
        domain = os.environ.get("REPL_SLUG", "")
        owner = os.environ.get("REPL_OWNER", "")
        if domain and owner:
            self.base_url = base_url or f"https://{domain}.{owner}.repl.co"
        else:
            # Check if PORT is set in environment and use it
            port = os.environ.get("PORT", "8501")  # Use port 8501
            self.base_url = base_url or os.environ.get("API_BASE_URL", f"http://localhost:{port}")
    
    def test_llm(self, prompt: str, provider: str = "together") -> Dict[str, Any]:
        """Test LLM provider"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/llm",
                params={"prompt": prompt, "provider": provider},
                timeout=30
            )
            
            # Check if response is successful
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
            # Try to parse JSON response
            try:
                json_response = response.json()
                # Check if it's an unexpected response format
                if "code" in json_response and "message" in json_response:
                    return {"success": False, "error": f"Unexpected response: {json_response}"}
                return json_response
            except ValueError as e:
                return {"success": False, "error": f"Invalid JSON response: {response.text}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error - is the API server running?"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_github(self, repository: str) -> Dict[str, Any]:
        """Test GitHub integration"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/github",
                params={"repository": repository},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_jira(self, project_key: str) -> Dict[str, Any]:
        """Test Jira integration"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/jira",
                params={"project_key": project_key},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_confluence(self, space_key: str) -> Dict[str, Any]:
        """Test Confluence integration"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/confluence",
                params={"space_key": space_key},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_grafana(self) -> Dict[str, Any]:
        """Test Grafana integration"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/grafana",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_context_resolver(self, issue_id: str, source: str, repository: str = "") -> Dict[str, Any]:
        """Test context resolver"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/context-resolver",
                params={"issue_id": issue_id, "source": source, "repository": repository},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_code_analysis(self, code: str, context: str) -> Dict[str, Any]:
        """Test code analysis"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/code-analysis",
                params={"code": code, "context": context},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_generate_tests(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Test test generation"""
        try:
            response = requests.post(
                f"{self.base_url}/api/test/generate-tests",
                params={"code": code, "language": language},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_issue(
        self,
        issue_id: str,
        source: str,
        repository: str = "",
        create_pr: bool = False,
        publish_docs: bool = False,
        confluence_space: Optional[str] = None
    ) -> Dict[str, Any]:
        """Full issue analysis"""
        try:
            response = requests.post(
                f"{self.base_url}/api/analyze",
                json={
                    "issue_id": issue_id,
                    "source": source,
                    "repository": repository,
                    "create_pr": create_pr,
                    "publish_docs": publish_docs,
                    "confluence_space": confluence_space
                },
                timeout=60
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_health(self) -> Dict[str, Any]:
        """Get API health status"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
