import re
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
import chromadb
from chromadb.config import Settings
import hashlib


class KnowledgeExtractor:
    """Extracts and processes knowledge from documents"""
    
    def __init__(self, chroma_path: str = "./knowledge/chromadb"):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize ChromaDB with persistent storage
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collections for different knowledge types
        self.collections = {}
        
    def get_or_create_collection(self, name: str, description: str = "") -> chromadb.Collection:
        """Get or create a ChromaDB collection"""
        if name not in self.collections:
            try:
                self.collections[name] = self.chroma_client.get_collection(name)
            except:
                self.collections[name] = self.chroma_client.create_collection(
                    name=name,
                    metadata={"description": description}
                )
        return self.collections[name]
    
    def process_lessons_learned(self, docs: List[Dict]) -> Dict[str, Any]:
        """Extract key lessons and patterns"""
        collection = self.get_or_create_collection(
            "lessons_learned",
            "Architectural decisions and lessons from VideoCommentator"
        )
        
        processed_count = 0
        extracted_lessons = []
        
        for doc in docs:
            # Extract specific patterns
            lessons = self._extract_lessons(doc['content'])
            
            for lesson in lessons:
                # Create unique ID for deduplication
                lesson_id = self._generate_id(doc['path'], lesson['text'])
                
                # Create embedding and store
                try:
                    embedding = self.embeddings.embed_query(lesson['text'])
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[lesson['text']],
                        metadatas=[{
                            "source": doc['path'],
                            "type": lesson['type'],
                            "importance": lesson['importance'],
                            "context": lesson.get('context', ''),
                            "extracted_at": datetime.now().isoformat(),
                            "title": doc.get('title', '')
                        }],
                        ids=[lesson_id]
                    )
                    
                    extracted_lessons.append({
                        "id": lesson_id,
                        "type": lesson['type'],
                        "source": doc['path']
                    })
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing lesson from {doc['path']}: {e}")
                    continue
        
        return {
            "collection": "lessons_learned",
            "processed_count": processed_count,
            "total_docs": len(docs),
            "extracted_lessons": extracted_lessons
        }
    
    def process_category(self, category: str, documents: List[Dict]) -> Dict[str, Any]:
        """Process documents by category"""
        # Map categories to processing methods
        processors = {
            "lessons_learned": self.process_lessons_learned,
            "architectural_decisions": self.process_architectural_decisions,
            "implementation_guides": self.process_implementation_guides,
            "api_documentation": self.process_api_documentation,
            "known_issues": self.process_known_issues,
            "configuration_patterns": self.process_configuration_patterns,
            "ui_patterns": self.process_ui_patterns,
            "deployment_scripts": self.process_deployment_scripts
        }
        
        processor = processors.get(category, self.process_generic_documents)
        return processor(documents)
    
    def process_architectural_decisions(self, docs: List[Dict]) -> Dict[str, Any]:
        """Process architectural decision documents"""
        collection = self.get_or_create_collection(
            "architectural_decisions",
            "Architecture patterns and design decisions"
        )
        
        processed_count = 0
        decisions = []
        
        for doc in docs:
            # Extract ADRs (Architecture Decision Records)
            extracted = self._extract_architectural_patterns(doc['content'])
            
            for decision in extracted:
                decision_id = self._generate_id(doc['path'], decision['title'])
                
                try:
                    # Create a comprehensive text for embedding
                    full_text = f"{decision['title']}\n\n{decision['context']}\n\n{decision['decision']}"
                    embedding = self.embeddings.embed_query(full_text)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[full_text],
                        metadatas=[{
                            "source": doc['path'],
                            "title": decision['title'],
                            "type": "architecture_decision",
                            "components": json.dumps(decision.get('components', [])),
                            "rationale": decision.get('rationale', ''),
                            "consequences": json.dumps(decision.get('consequences', {})),
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[decision_id]
                    )
                    
                    decisions.append(decision)
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing architectural decision: {e}")
                    continue
        
        return {
            "collection": "architectural_decisions",
            "processed_count": processed_count,
            "total_docs": len(docs),
            "decisions": decisions
        }
    
    def process_implementation_guides(self, docs: List[Dict]) -> Dict[str, Any]:
        """Process implementation guide documents"""
        collection = self.get_or_create_collection(
            "implementation_guides",
            "How-to guides and implementation patterns"
        )
        
        processed_count = 0
        
        for doc in docs:
            # Split into chunks for better retrieval
            chunks = self.text_splitter.split_text(doc['content'])
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{self._generate_id(doc['path'], chunk)}_{i}"
                
                try:
                    embedding = self.embeddings.embed_query(chunk)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{
                            "source": doc['path'],
                            "title": doc.get('title', ''),
                            "type": "implementation_guide",
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "priority": doc.get('priority', False),
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[chunk_id]
                    )
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing implementation guide chunk: {e}")
                    continue
        
        return {
            "collection": "implementation_guides",
            "processed_count": processed_count,
            "total_docs": len(docs)
        }
    
    def process_api_documentation(self, docs: List[Dict]) -> Dict[str, Any]:
        """Process API documentation"""
        collection = self.get_or_create_collection(
            "api_documentation",
            "API endpoints, request/response formats, and patterns"
        )
        
        processed_count = 0
        endpoints = []
        
        for doc in docs:
            # Extract API patterns
            extracted_endpoints = self._extract_api_patterns(doc['content'])
            
            for endpoint in extracted_endpoints:
                endpoint_id = self._generate_id(
                    doc['path'], 
                    f"{endpoint['method']}_{endpoint['path']}"
                )
                
                try:
                    # Create searchable text
                    endpoint_text = (
                        f"{endpoint['method']} {endpoint['path']}\n"
                        f"Description: {endpoint.get('description', '')}\n"
                        f"Parameters: {json.dumps(endpoint.get('parameters', {}))}\n"
                        f"Response: {endpoint.get('response', '')}"
                    )
                    
                    embedding = self.embeddings.embed_query(endpoint_text)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[endpoint_text],
                        metadatas=[{
                            "source": doc['path'],
                            "method": endpoint['method'],
                            "path": endpoint['path'],
                            "type": "api_endpoint",
                            "parameters": json.dumps(endpoint.get('parameters', {})),
                            "response_format": endpoint.get('response', ''),
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[endpoint_id]
                    )
                    
                    endpoints.append(endpoint)
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing API endpoint: {e}")
                    continue
        
        return {
            "collection": "api_documentation",
            "processed_count": processed_count,
            "total_docs": len(docs),
            "endpoints": endpoints
        }
    
    def process_known_issues(self, docs: List[Dict]) -> Dict[str, Any]:
        """Process known issues and bug reports"""
        collection = self.get_or_create_collection(
            "known_issues",
            "Known issues, bugs, and their workarounds"
        )
        
        processed_count = 0
        issues = []
        
        for doc in docs:
            # Extract issues and solutions
            extracted_issues = self._extract_issues(doc['content'])
            
            for issue in extracted_issues:
                issue_id = self._generate_id(doc['path'], issue['description'])
                
                try:
                    # Create searchable text
                    issue_text = (
                        f"Issue: {issue['description']}\n"
                        f"Category: {issue.get('category', 'general')}\n"
                        f"Solution: {issue.get('solution', 'No solution provided')}\n"
                        f"Workaround: {issue.get('workaround', 'No workaround available')}"
                    )
                    
                    embedding = self.embeddings.embed_query(issue_text)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[issue_text],
                        metadatas=[{
                            "source": doc['path'],
                            "category": issue.get('category', 'general'),
                            "severity": issue.get('severity', 'medium'),
                            "type": "known_issue",
                            "has_solution": bool(issue.get('solution')),
                            "has_workaround": bool(issue.get('workaround')),
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[issue_id]
                    )
                    
                    issues.append(issue)
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing known issue: {e}")
                    continue
        
        return {
            "collection": "known_issues",
            "processed_count": processed_count,
            "total_docs": len(docs),
            "issues": issues
        }
    
    def process_configuration_patterns(self, docs: List[Dict]) -> Dict[str, Any]:
        """Process configuration patterns"""
        collection = self.get_or_create_collection(
            "configuration_patterns",
            "Configuration patterns and best practices"
        )
        
        processed_count = 0
        
        for doc in docs:
            # Extract configuration examples
            configs = self._extract_configuration_patterns(doc['content'])
            
            for config in configs:
                config_id = self._generate_id(doc['path'], config['name'])
                
                try:
                    config_text = (
                        f"Configuration: {config['name']}\n"
                        f"Type: {config['type']}\n"
                        f"Description: {config.get('description', '')}\n"
                        f"Example:\n{config.get('example', '')}"
                    )
                    
                    embedding = self.embeddings.embed_query(config_text)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[config_text],
                        metadatas=[{
                            "source": doc['path'],
                            "config_type": config['type'],
                            "name": config['name'],
                            "type": "configuration",
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[config_id]
                    )
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing configuration pattern: {e}")
                    continue
        
        return {
            "collection": "configuration_patterns",
            "processed_count": processed_count,
            "total_docs": len(docs)
        }
    
    def process_ui_patterns(self, docs: List[Dict]) -> Dict[str, Any]:
        """Process UI/frontend patterns"""
        collection = self.get_or_create_collection(
            "ui_patterns",
            "Frontend components and UI patterns"
        )
        
        processed_count = 0
        
        for doc in docs:
            # Split into chunks
            chunks = self.text_splitter.split_text(doc['content'])
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{self._generate_id(doc['path'], chunk)}_{i}"
                
                try:
                    embedding = self.embeddings.embed_query(chunk)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{
                            "source": doc['path'],
                            "title": doc.get('title', ''),
                            "type": "ui_pattern",
                            "chunk_index": i,
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[chunk_id]
                    )
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing UI pattern: {e}")
                    continue
        
        return {
            "collection": "ui_patterns",
            "processed_count": processed_count,
            "total_docs": len(docs)
        }
    
    def process_deployment_scripts(self, docs: List[Dict]) -> Dict[str, Any]:
        """Process deployment scripts and patterns"""
        collection = self.get_or_create_collection(
            "deployment_scripts",
            "Deployment scripts and CI/CD patterns"
        )
        
        processed_count = 0
        
        for doc in docs:
            # Extract deployment patterns
            patterns = self._extract_deployment_patterns(doc['content'])
            
            for pattern in patterns:
                pattern_id = self._generate_id(doc['path'], pattern['name'])
                
                try:
                    pattern_text = (
                        f"Deployment Pattern: {pattern['name']}\n"
                        f"Type: {pattern['type']}\n"
                        f"Description: {pattern.get('description', '')}\n"
                        f"Steps:\n{pattern.get('steps', '')}"
                    )
                    
                    embedding = self.embeddings.embed_query(pattern_text)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[pattern_text],
                        metadatas=[{
                            "source": doc['path'],
                            "pattern_type": pattern['type'],
                            "name": pattern['name'],
                            "type": "deployment_pattern",
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[pattern_id]
                    )
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing deployment pattern: {e}")
                    continue
        
        return {
            "collection": "deployment_scripts",
            "processed_count": processed_count,
            "total_docs": len(docs)
        }
    
    def process_generic_documents(self, docs: List[Dict]) -> Dict[str, Any]:
        """Generic document processor for uncategorized content"""
        collection = self.get_or_create_collection(
            "general_knowledge",
            "General knowledge and documentation"
        )
        
        processed_count = 0
        
        for doc in docs:
            chunks = self.text_splitter.split_text(doc['content'])
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{self._generate_id(doc['path'], chunk)}_{i}"
                
                try:
                    embedding = self.embeddings.embed_query(chunk)
                    
                    collection.add(
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{
                            "source": doc['path'],
                            "title": doc.get('title', ''),
                            "type": "general",
                            "chunk_index": i,
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[chunk_id]
                    )
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing document chunk: {e}")
                    continue
        
        return {
            "collection": "general_knowledge",
            "processed_count": processed_count,
            "total_docs": len(docs)
        }
    
    def _extract_lessons(self, content: str) -> List[Dict]:
        """Extract specific lessons from content"""
        lessons = []
        
        if not content:
            return lessons
        
        # Pattern matching for different lesson types
        patterns = {
            "bug_fix": r"(?:Fixed|Resolved|Solution):\s*(.+?)(?:\n\n|$)",
            "best_practice": r"(?:Best Practice|Always|Should):\s*(.+?)(?:\n\n|$)",
            "warning": r"(?:Warning|Caution|Important|IMPORTANT):\s*(.+?)(?:\n\n|$)",
            "pattern": r"(?:Pattern|Approach|Strategy):\s*(.+?)(?:\n\n|$)",
            "lesson": r"(?:Lesson|Learned|Key Takeaway):\s*(.+?)(?:\n\n|$)",
            "pitfall": r"(?:Pitfall|Avoid|Don't|Never):\s*(.+?)(?:\n\n|$)"
        }
        
        # Extract based on patterns
        for lesson_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                lesson_text = match.group(1).strip()
                
                # Skip very short lessons
                if len(lesson_text) < 20:
                    continue
                
                # Extract context (surrounding text)
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end].strip()
                
                lessons.append({
                    "type": lesson_type,
                    "text": lesson_text,
                    "importance": self._calculate_importance(lesson_text, lesson_type),
                    "context": context,
                    "id": hashlib.md5(lesson_text.encode()).hexdigest()[:8]
                })
        
        # Also look for numbered lists of lessons
        numbered_patterns = [
            r"(\d+)\.\s*(.+?)(?=\n\d+\.|$)",
            r"[-*]\s*(.+?)(?=\n[-*]|$)"
        ]
        
        for pattern in numbered_patterns:
            if "lessons" in content.lower() or "learned" in content.lower():
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    lesson_text = match.group(2 if "\\d+" in pattern else 1).strip()
                    
                    if len(lesson_text) > 20 and len(lesson_text) < 500:
                        lessons.append({
                            "type": "lesson",
                            "text": lesson_text,
                            "importance": 3,
                            "context": "",
                            "id": hashlib.md5(lesson_text.encode()).hexdigest()[:8]
                        })
        
        return lessons
    
    def _extract_architectural_patterns(self, content: str) -> List[Dict]:
        """Extract architectural decisions and patterns"""
        decisions = []
        
        if not content:
            return decisions
        
        # Look for ADR-style sections
        adr_pattern = r"##\s*(?:Decision|Architecture|Design)(?:\s+\d+)?:\s*(.+?)\n(.*?)(?=##|$)"
        matches = re.finditer(adr_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            title = match.group(1).strip()
            body = match.group(2).strip()
            
            decision = {
                "title": title,
                "context": "",
                "decision": "",
                "rationale": "",
                "consequences": {"positive": [], "negative": []},
                "components": []
            }
            
            # Extract context
            context_match = re.search(r"(?:Context|Background):\s*(.+?)(?=\n#|Decision:|$)", body, re.DOTALL | re.IGNORECASE)
            if context_match:
                decision["context"] = context_match.group(1).strip()
            
            # Extract decision
            decision_match = re.search(r"(?:Decision|Solution|Approach):\s*(.+?)(?=\n#|Rationale:|$)", body, re.DOTALL | re.IGNORECASE)
            if decision_match:
                decision["decision"] = decision_match.group(1).strip()
            
            # Extract rationale
            rationale_match = re.search(r"(?:Rationale|Reasoning|Why):\s*(.+?)(?=\n#|Consequences:|$)", body, re.DOTALL | re.IGNORECASE)
            if rationale_match:
                decision["rationale"] = rationale_match.group(1).strip()
            
            # Extract consequences
            consequences_match = re.search(r"(?:Consequences|Impact|Results):\s*(.+?)(?=\n#|$)", body, re.DOTALL | re.IGNORECASE)
            if consequences_match:
                cons_text = consequences_match.group(1)
                # Look for positive/negative markers
                positive = re.findall(r"(?:Positive|\+|Pros?):\s*(.+?)(?=Negative|-|Cons?:|$)", cons_text, re.DOTALL | re.IGNORECASE)
                negative = re.findall(r"(?:Negative|-|Cons?):\s*(.+?)(?=Positive|\+|Pros?:|$)", cons_text, re.DOTALL | re.IGNORECASE)
                
                if positive:
                    decision["consequences"]["positive"] = [p.strip() for p in positive[0].split("\n") if p.strip()]
                if negative:
                    decision["consequences"]["negative"] = [n.strip() for n in negative[0].split("\n") if n.strip()]
            
            # Extract affected components
            components = re.findall(r"(?:Component|Service|Module):\s*(\w+)", body, re.IGNORECASE)
            decision["components"] = list(set(components))
            
            decisions.append(decision)
        
        return decisions
    
    def _extract_api_patterns(self, content: str) -> List[Dict]:
        """Extract API endpoint patterns"""
        endpoints = []
        
        if not content:
            return endpoints
        
        # Pattern for API documentation
        api_patterns = [
            r"(?:GET|POST|PUT|DELETE|PATCH)\s+([/\w\{\}]+)",
            r"`(?:GET|POST|PUT|DELETE|PATCH)\s+([/\w\{\}]+)`",
            r"@(?:Get|Post|Put|Delete|Patch)\s*\(\s*['\"]([/\w\{\}]+)"
        ]
        
        for pattern in api_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                method = re.search(r"(GET|POST|PUT|DELETE|PATCH)", match.group(0), re.IGNORECASE)
                if method:
                    endpoint = {
                        "method": method.group(1).upper(),
                        "path": match.group(1),
                        "description": "",
                        "parameters": {},
                        "response": ""
                    }
                    
                    # Try to extract description (look ahead for description text)
                    desc_pattern = rf"{re.escape(match.group(0))}\s*(?::|-)?\s*(.+?)(?=\n|$)"
                    desc_match = re.search(desc_pattern, content)
                    if desc_match:
                        endpoint["description"] = desc_match.group(1).strip()
                    
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_issues(self, content: str) -> List[Dict]:
        """Extract known issues and their solutions"""
        issues = []
        
        if not content:
            return issues
        
        # Patterns for issues
        issue_patterns = [
            r"(?:Issue|Problem|Bug):\s*(.+?)(?:Solution|Fix|Workaround):\s*(.+?)(?=Issue|Problem|Bug|$)",
            r"###?\s*(.+?)\n.*?(?:Solution|Fix|Workaround):\s*(.+?)(?=###?|$)",
            r"(?:Known Issue|Bug):\s*(.+?)(?=\n|$)"
        ]
        
        for pattern in issue_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                issue = {
                    "description": match.group(1).strip(),
                    "solution": match.group(2).strip() if match.lastindex >= 2 else "",
                    "category": self._categorize_issue(match.group(1)),
                    "severity": self._assess_severity(match.group(1))
                }
                
                # Look for workaround if no solution
                if not issue["solution"]:
                    workaround_pattern = rf"{re.escape(match.group(1))}.+?Workaround:\s*(.+?)(?=\n\n|$)"
                    workaround_match = re.search(workaround_pattern, content, re.DOTALL | re.IGNORECASE)
                    if workaround_match:
                        issue["workaround"] = workaround_match.group(1).strip()
                
                issues.append(issue)
        
        return issues
    
    def _extract_configuration_patterns(self, content: str) -> List[Dict]:
        """Extract configuration patterns and examples"""
        configs = []
        
        if not content:
            return configs
        
        # Look for configuration blocks
        config_patterns = [
            r"```(?:yaml|yml|json|env|ini|toml)\n(.+?)```",
            r"(?:Configuration|Config|Settings):\s*\n(.+?)(?=\n\n|$)"
        ]
        
        for pattern in config_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                config_content = match.group(1).strip()
                
                # Determine config type
                config_type = "unknown"
                if "```" in match.group(0):
                    type_match = re.search(r"```(\w+)", match.group(0))
                    if type_match:
                        config_type = type_match.group(1)
                elif any(x in config_content for x in ["image:", "container_name:", "services:"]):
                    config_type = "docker"
                elif any(x in config_content for x in ["[", "]"]) and "=" in config_content:
                    config_type = "ini"
                elif "{" in config_content and "}" in config_content:
                    config_type = "json"
                
                # Extract name from preceding text
                name_pattern = r"(?:###?\s*)?(\w[\w\s-]+?)(?:\n|:)"
                preceding_text = content[max(0, match.start()-100):match.start()]
                name_match = re.search(name_pattern, preceding_text[::-1])
                
                config_name = "Configuration"
                if name_match:
                    config_name = name_match.group(1)[::-1].strip()
                
                configs.append({
                    "name": config_name,
                    "type": config_type,
                    "example": config_content,
                    "description": ""
                })
        
        return configs
    
    def _extract_deployment_patterns(self, content: str) -> List[Dict]:
        """Extract deployment patterns and scripts"""
        patterns = []
        
        if not content:
            return patterns
        
        # Look for deployment sections
        deploy_sections = re.finditer(
            r"(?:Deploy|Deployment|CI/CD)(?:\s+\w+)?:\s*\n(.+?)(?=\n#|$)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        for section in deploy_sections:
            section_content = section.group(1)
            
            # Extract steps
            steps = []
            step_pattern = r"(?:\d+\.|[-*])\s*(.+?)(?=\n(?:\d+\.|[-*])|$)"
            step_matches = re.finditer(step_pattern, section_content, re.MULTILINE)
            
            for step_match in step_matches:
                steps.append(step_match.group(1).strip())
            
            pattern_name = "Deployment Process"
            name_match = re.search(r"(?:Deploy|Deployment)\s+(\w+)", section.group(0), re.IGNORECASE)
            if name_match:
                pattern_name = f"{name_match.group(1)} Deployment"
            
            patterns.append({
                "name": pattern_name,
                "type": "deployment",
                "description": section_content.split("\n")[0] if section_content else "",
                "steps": "\n".join(steps)
            })
        
        # Also look for GitHub Actions workflows
        if "jobs:" in content and "steps:" in content:
            workflow_name = "GitHub Actions Workflow"
            name_match = re.search(r"name:\s*(.+)", content)
            if name_match:
                workflow_name = name_match.group(1).strip()
            
            patterns.append({
                "name": workflow_name,
                "type": "github-actions",
                "description": "CI/CD workflow",
                "steps": content
            })
        
        return patterns
    
    def _calculate_importance(self, text: str, lesson_type: str) -> int:
        """Calculate importance score (1-5) based on content and type"""
        importance = 3  # Default
        
        # Type-based scoring
        type_scores = {
            "bug_fix": 4,
            "warning": 5,
            "pitfall": 5,
            "best_practice": 4,
            "pattern": 3,
            "lesson": 3
        }
        
        importance = type_scores.get(lesson_type, 3)
        
        # Adjust based on keywords
        high_priority_keywords = ["critical", "important", "must", "always", "never", "security", "performance"]
        medium_priority_keywords = ["should", "recommend", "prefer", "consider"]
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in high_priority_keywords):
            importance = min(5, importance + 1)
        elif any(keyword in text_lower for keyword in medium_priority_keywords):
            importance = max(1, importance - 1)
        
        return importance
    
    def _categorize_issue(self, description: str) -> str:
        """Categorize issue based on description"""
        description_lower = description.lower()
        
        categories = {
            "performance": ["slow", "performance", "speed", "timeout", "memory", "cpu"],
            "security": ["security", "vulnerability", "auth", "permission", "access"],
            "data": ["data", "database", "corruption", "loss", "integrity"],
            "api": ["api", "endpoint", "request", "response", "rest"],
            "ui": ["ui", "frontend", "display", "render", "css", "javascript"],
            "deployment": ["deploy", "build", "ci", "cd", "docker", "kubernetes"],
            "integration": ["integration", "third-party", "external", "service"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _assess_severity(self, description: str) -> str:
        """Assess issue severity based on description"""
        description_lower = description.lower()
        
        high_severity_keywords = ["critical", "crash", "data loss", "security", "vulnerability", "broken"]
        medium_severity_keywords = ["error", "fail", "issue", "problem", "bug"]
        low_severity_keywords = ["minor", "cosmetic", "typo", "improvement"]
        
        if any(keyword in description_lower for keyword in high_severity_keywords):
            return "high"
        elif any(keyword in description_lower for keyword in low_severity_keywords):
            return "low"
        elif any(keyword in description_lower for keyword in medium_severity_keywords):
            return "medium"
        
        return "medium"
    
    def _generate_id(self, source: str, content: str) -> str:
        """Generate unique ID for content"""
        combined = f"{source}:{content[:100]}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]