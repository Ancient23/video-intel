import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import frontmatter
import re
from datetime import datetime


class DocumentInventory:
    """Inventories all documentation from the old repository"""
    
    def __init__(self, old_repo_path: str):
        self.old_repo_path = Path(old_repo_path)
        self.docs_path = self.old_repo_path / "apps" / "web" / "docs"
        
    def scan_documentation(self) -> Dict[str, List[Dict]]:
        """Scan all documentation and categorize by type"""
        inventory = {
            "lessons_learned": [],
            "architectural_decisions": [],
            "implementation_guides": [],
            "api_documentation": [],
            "deployment_scripts": [],
            "configuration_patterns": [],
            "ui_patterns": [],
            "known_issues": []
        }
        
        # Key files to prioritize
        priority_files = [
            "history/lessons-learned.md",
            "reference/architecture.md",
            "reference/api.md",
            "guides/operations/pydantic-v2.md",
            "planning/known-issues.md",
            "reference/design/design-system.md",
            "current/implementation-plan.md"
        ]
        
        # Check if docs path exists
        if not self.docs_path.exists():
            print(f"Warning: Documentation path does not exist: {self.docs_path}")
            return inventory
            
        # Scan all markdown files
        for md_file in self.docs_path.rglob("*.md"):
            try:
                relative_path = md_file.relative_to(self.docs_path)
                
                # Read and parse frontmatter if exists
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    
                doc_info = {
                    "path": str(relative_path),
                    "full_path": str(md_file),
                    "title": post.get('title', md_file.stem),
                    "content": post.content,
                    "metadata": post.metadata,
                    "category": self._categorize_document(relative_path, post.content),
                    "priority": str(relative_path) in priority_files,
                    "file_size": md_file.stat().st_size,
                    "last_modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
                }
                
                category = doc_info["category"]
                if category in inventory:
                    inventory[category].append(doc_info)
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
                continue
                
        return inventory
    
    def _categorize_document(self, path: Path, content: str) -> str:
        """Categorize document based on path and content"""
        path_str = str(path).lower()
        content_lower = content.lower() if content else ""
        
        # Path-based categorization
        if "lessons" in path_str or "learned" in path_str:
            return "lessons_learned"
        elif "architecture" in path_str or "design" in path_str and "system" in path_str:
            return "architectural_decisions"
        elif "guide" in path_str or "how-to" in path_str or "tutorial" in path_str:
            return "implementation_guides"
        elif "api" in path_str or "endpoint" in path_str:
            return "api_documentation"
        elif "deploy" in path_str or "ci" in path_str:
            return "deployment_scripts"
        elif "config" in path_str or "settings" in path_str:
            return "configuration_patterns"
        elif "ui" in path_str or "component" in path_str or "frontend" in path_str:
            return "ui_patterns"
        elif "issue" in path_str or "bug" in path_str or "problem" in path_str:
            return "known_issues"
        
        # Content-based categorization
        if "lesson" in content_lower or "learned" in content_lower:
            return "lessons_learned"
        elif "architecture" in content_lower or "decision" in content_lower:
            return "architectural_decisions"
        elif "api" in content_lower and ("endpoint" in content_lower or "route" in content_lower):
            return "api_documentation"
        elif "known issue" in content_lower or "bug" in content_lower:
            return "known_issues"
        
        # Default to implementation guides
        return "implementation_guides"
    
    def extract_code_patterns(self) -> Dict[str, List[Dict]]:
        """Extract reusable code patterns"""
        patterns = {
            "pydantic_models": [],
            "api_endpoints": [],
            "celery_tasks": [],
            "docker_configs": [],
            "deployment_scripts": [],
            "test_patterns": [],
            "utility_functions": []
        }
        
        # Extract from Python files
        backend_path = self.old_repo_path / "services" / "backend"
        
        if backend_path.exists():
            # Pydantic models
            for py_file in backend_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    relative_path = py_file.relative_to(self.old_repo_path)
                    
                    # Check for Pydantic models
                    if "BaseModel" in content or "pydantic" in content:
                        # Extract class definitions
                        model_matches = re.findall(
                            r'class\s+(\w+).*?(?:BaseModel|BaseSettings).*?:\n((?:\s{4,}.*\n)*)',
                            content,
                            re.MULTILINE
                        )
                        
                        if model_matches:
                            patterns["pydantic_models"].append({
                                "file": str(relative_path),
                                "models": [m[0] for m in model_matches],
                                "content": content,
                                "extracted_at": datetime.now().isoformat()
                            })
                    
                    # Check for API endpoints
                    if "@router" in content or "@app" in content:
                        endpoint_matches = re.findall(
                            r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
                            content
                        )
                        
                        if endpoint_matches:
                            patterns["api_endpoints"].append({
                                "file": str(relative_path),
                                "endpoints": [{"method": m[0], "path": m[1]} for m in endpoint_matches],
                                "content": content,
                                "extracted_at": datetime.now().isoformat()
                            })
                    
                    # Check for Celery tasks
                    if "@celery" in content or "@task" in content:
                        task_matches = re.findall(
                            r'@(?:celery_app\.)?task.*?\ndef\s+(\w+)',
                            content,
                            re.MULTILINE
                        )
                        
                        if task_matches:
                            patterns["celery_tasks"].append({
                                "file": str(relative_path),
                                "tasks": task_matches,
                                "content": content,
                                "extracted_at": datetime.now().isoformat()
                            })
                    
                    # Check for test patterns
                    if "pytest" in content or "unittest" in content or "def test_" in content:
                        test_matches = re.findall(
                            r'def\s+(test_\w+)',
                            content
                        )
                        
                        if test_matches:
                            patterns["test_patterns"].append({
                                "file": str(relative_path),
                                "tests": test_matches,
                                "content": content,
                                "extracted_at": datetime.now().isoformat()
                            })
                    
                except Exception as e:
                    print(f"Error processing Python file {py_file}: {e}")
                    continue
        
        # Docker configurations
        docker_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "Dockerfile",
            "**/Dockerfile",
            "**/*.dockerfile"
        ]
        
        for pattern in docker_files:
            for docker_file in self.old_repo_path.glob(pattern):
                try:
                    patterns["docker_configs"].append({
                        "file": str(docker_file.relative_to(self.old_repo_path)),
                        "content": docker_file.read_text(encoding='utf-8'),
                        "type": "Dockerfile" if "Dockerfile" in docker_file.name else "docker-compose",
                        "extracted_at": datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error processing Docker file {docker_file}: {e}")
                    continue
        
        # Deployment scripts
        deployment_patterns = ["deploy*.sh", "**/*deploy*.sh", ".github/workflows/*.yml"]
        
        for pattern in deployment_patterns:
            for script in self.old_repo_path.glob(pattern):
                try:
                    patterns["deployment_scripts"].append({
                        "file": str(script.relative_to(self.old_repo_path)),
                        "content": script.read_text(encoding='utf-8'),
                        "type": "shell" if script.suffix == ".sh" else "github-action",
                        "extracted_at": datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error processing deployment script {script}: {e}")
                    continue
                    
        return patterns
    
    def extract_configuration_patterns(self) -> Dict[str, List[Dict]]:
        """Extract configuration patterns from various config files"""
        configs = {
            "environment_variables": [],
            "aws_configs": [],
            "database_configs": [],
            "api_configs": []
        }
        
        # Environment files
        env_files = [".env", ".env.example", "**/.env", "**/.env.example"]
        for pattern in env_files:
            for env_file in self.old_repo_path.glob(pattern):
                try:
                    content = env_file.read_text(encoding='utf-8')
                    # Extract variable names (not values for security)
                    var_names = re.findall(r'^([A-Z_]+)=', content, re.MULTILINE)
                    
                    configs["environment_variables"].append({
                        "file": str(env_file.relative_to(self.old_repo_path)),
                        "variables": var_names,
                        "extracted_at": datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error processing env file {env_file}: {e}")
                    continue
        
        # AWS task definitions
        aws_patterns = ["aws-task-definition*.json", "**/task-definition*.json"]
        for pattern in aws_patterns:
            for aws_file in self.old_repo_path.glob(pattern):
                try:
                    content = json.loads(aws_file.read_text(encoding='utf-8'))
                    configs["aws_configs"].append({
                        "file": str(aws_file.relative_to(self.old_repo_path)),
                        "service": content.get("family", "unknown"),
                        "cpu": content.get("cpu"),
                        "memory": content.get("memory"),
                        "extracted_at": datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error processing AWS config {aws_file}: {e}")
                    continue
                    
        return configs
    
    def generate_inventory_report(self, inventory: Dict[str, List[Dict]]) -> Dict:
        """Generate a summary report of the inventory"""
        report = {
            "total_documents": sum(len(docs) for docs in inventory.values()),
            "categories": {},
            "priority_documents": [],
            "generated_at": datetime.now().isoformat()
        }
        
        for category, docs in inventory.items():
            if docs:
                report["categories"][category] = {
                    "count": len(docs),
                    "total_size": sum(doc.get("file_size", 0) for doc in docs),
                    "files": [doc["path"] for doc in docs]
                }
                
                # Collect priority documents
                priority_docs = [doc for doc in docs if doc.get("priority", False)]
                report["priority_documents"].extend([{
                    "category": category,
                    "path": doc["path"],
                    "title": doc["title"]
                } for doc in priority_docs])
        
        return report