"""
Graph Extractor for Knowledge Base

Extracts entities and relationships from text for Graph-RAG.
"""
import re
from typing import List, Dict, Tuple, Any
import spacy
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class GraphExtractor:
    """Extract entities and relationships from text"""
    
    def __init__(self, use_spacy: bool = True):
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("SpaCy NLP model loaded")
            except:
                logger.warning("SpaCy not available, falling back to pattern matching")
                self.use_spacy = False
                self.nlp = None
    
    def extract_entities_and_relationships(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract entities and relationships from text
        
        Args:
            text: Text to process
            context: Additional context (title, category, etc.)
            
        Returns:
            Dictionary with entities and relationships
        """
        entities = []
        relationships = []
        
        if self.use_spacy and self.nlp:
            # Use SpaCy for advanced extraction
            entities, relationships = self._extract_with_spacy(text)
        else:
            # Fallback to pattern matching
            entities = self._extract_entities_pattern(text)
            relationships = self._extract_relationships_pattern(text, entities)
        
        # Add domain-specific entities
        domain_entities = self._extract_domain_entities(text, context)
        entities.extend(domain_entities)
        
        # Deduplicate
        entities = self._deduplicate_entities(entities)
        relationships = self._deduplicate_relationships(relationships)
        
        return {
            "entities": entities,
            "relationships": relationships,
            "stats": {
                "entity_count": len(entities),
                "relationship_count": len(relationships)
            }
        }
    
    def _extract_with_spacy(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """Extract using SpaCy NLP"""
        doc = self.nlp(text)
        entities = []
        relationships = []
        
        # Extract named entities
        for ent in doc.ents:
            entity_type = self._map_spacy_type(ent.label_)
            if entity_type:
                entities.append({
                    "name": ent.text,
                    "type": entity_type,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        
        # Extract relationships from dependency parsing
        for token in doc:
            if token.dep_ in ["nsubj", "dobj", "pobj"]:
                # Subject-Verb-Object patterns
                if token.head.pos_ == "VERB":
                    subject = None
                    obj = None
                    
                    for child in token.head.children:
                        if child.dep_ == "nsubj":
                            subject = child.text
                        elif child.dep_ in ["dobj", "pobj"]:
                            obj = child.text
                    
                    if subject and obj:
                        relationships.append({
                            "source": subject,
                            "target": obj,
                            "type": token.head.lemma_,
                            "context": token.head.text
                        })
        
        return entities, relationships
    
    def _extract_entities_pattern(self, text: str) -> List[Dict[str, str]]:
        """Extract entities using pattern matching"""
        entities = []
        
        # Technology/Framework patterns
        tech_patterns = {
            "framework": [
                r'\b(FastAPI|Django|Flask|React|Vue|Angular|Next\.js)\b',
                r'\b(LangChain|Hugging Face|PyTorch|TensorFlow|Keras)\b',
            ],
            "database": [
                r'\b(MongoDB|PostgreSQL|MySQL|Redis|Neo4j|Qdrant|Pinecone|Milvus|ChromaDB)\b',
            ],
            "cloud": [
                r'\b(AWS|Azure|GCP|Google Cloud|Amazon Web Services)\b',
                r'\b(S3|EC2|Lambda|CloudFront|ECS|Fargate|RDS)\b',
            ],
            "ai_model": [
                r'\b(GPT-4|GPT-3\.5|Claude|LLaMA|BERT|T5|CLIP)\b',
                r'\b(OpenAI|Anthropic|Cohere|Stability AI)\b',
            ],
            "technology": [
                r'\b(Docker|Kubernetes|Jenkins|GitHub Actions|GitLab CI)\b',
                r'\b(Python|JavaScript|TypeScript|Go|Rust|Java)\b',
            ],
            "concept": [
                r'\b(RAG|Graph-RAG|embeddings?|vector search|semantic search)\b',
                r'\b(knowledge graph|machine learning|deep learning|NLP)\b',
                r'\b(microservices|API|REST|GraphQL|WebSocket)\b',
            ]
        }
        
        for entity_type, patterns in tech_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "name": match.group(),
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end()
                    })
        
        # Custom patterns for video intelligence domain
        video_patterns = {
            "video_concept": [
                r'\b(video chunk(?:ing)?|scene detection|shot boundary)\b',
                r'\b(frame extraction|video analysis|video processing)\b',
                r'\b(temporal segmentation|keyframe|thumbnail)\b',
            ],
            "ai_technique": [
                r'\b(object detection|scene classification|action recognition)\b',
                r'\b(video captioning|video summarization|visual QA)\b',
                r'\b(multimodal|vision-language|VLM|VILA)\b',
            ]
        }
        
        for entity_type, patterns in video_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "name": match.group(),
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end()
                    })
        
        return entities
    
    def _extract_relationships_pattern(self, text: str, entities: List[Dict]) -> List[Dict[str, str]]:
        """Extract relationships using pattern matching"""
        relationships = []
        
        # Relationship patterns
        rel_patterns = [
            # "X uses Y"
            (r'(\w+)\s+uses?\s+(\w+)', "uses"),
            # "X is based on Y"
            (r'(\w+)\s+is\s+based\s+on\s+(\w+)', "based_on"),
            # "X integrates with Y"
            (r'(\w+)\s+integrates?\s+with\s+(\w+)', "integrates_with"),
            # "X connects to Y"
            (r'(\w+)\s+connects?\s+to\s+(\w+)', "connects_to"),
            # "X depends on Y"
            (r'(\w+)\s+depends?\s+on\s+(\w+)', "depends_on"),
            # "X contains Y"
            (r'(\w+)\s+contains?\s+(\w+)', "contains"),
            # "X implements Y"
            (r'(\w+)\s+implements?\s+(\w+)', "implements"),
        ]
        
        # Entity names for quick lookup
        entity_names = {e["name"].lower() for e in entities}
        
        for pattern, rel_type in rel_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                source = match.group(1)
                target = match.group(2)
                
                # Check if both are known entities
                if source.lower() in entity_names or target.lower() in entity_names:
                    relationships.append({
                        "source": source,
                        "target": target,
                        "type": rel_type,
                        "context": match.group(0)
                    })
        
        return relationships
    
    def _extract_domain_entities(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """Extract domain-specific entities based on context"""
        entities = []
        
        if context:
            category = context.get("category", "").lower()
            
            # Category-specific extraction
            if "api" in category:
                # Extract API endpoints
                endpoint_pattern = r'(/api/[a-zA-Z0-9/_-]+|/v\d+/[a-zA-Z0-9/_-]+)'
                matches = re.finditer(endpoint_pattern, text)
                for match in matches:
                    entities.append({
                        "name": match.group(),
                        "type": "api_endpoint",
                        "start": match.start(),
                        "end": match.end()
                    })
            
            elif "video" in category:
                # Extract video-specific terms
                video_terms = ["codec", "resolution", "bitrate", "fps", "duration"]
                for term in video_terms:
                    if term in text.lower():
                        entities.append({
                            "name": term,
                            "type": "video_attribute",
                            "start": 0,
                            "end": 0
                        })
        
        return entities
    
    def _map_spacy_type(self, spacy_label: str) -> Optional[str]:
        """Map SpaCy entity types to our types"""
        mapping = {
            "ORG": "organization",
            "PERSON": "person",
            "GPE": "location",
            "LOC": "location",
            "PRODUCT": "technology",
            "WORK_OF_ART": "project",
            "LAW": "standard",
            "LANGUAGE": "technology",
            "DATE": "temporal",
            "TIME": "temporal",
            "PERCENT": "metric",
            "MONEY": "metric",
            "QUANTITY": "metric"
        }
        return mapping.get(spacy_label)
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = f"{entity['name'].lower()}:{entity['type']}"
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Remove duplicate relationships"""
        seen = set()
        unique_rels = []
        
        for rel in relationships:
            key = f"{rel['source'].lower()}:{rel['type']}:{rel['target'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_rels.append(rel)
        
        return unique_rels
    
    def extract_from_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Extract entities and relationships from code
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Extracted entities and relationships
        """
        entities = []
        relationships = []
        
        if language == "python":
            # Extract imports
            import_pattern = r'(?:from\s+(\S+)\s+)?import\s+([^#\n]+)'
            matches = re.finditer(import_pattern, code)
            
            for match in matches:
                module = match.group(1) or match.group(2).split()[0]
                entities.append({
                    "name": module,
                    "type": "module",
                    "start": match.start(),
                    "end": match.end()
                })
                
                # Add relationship
                relationships.append({
                    "source": "current_module",
                    "target": module,
                    "type": "imports",
                    "context": match.group(0).strip()
                })
            
            # Extract class definitions
            class_pattern = r'class\s+(\w+)(?:\(([^)]+)\))?:'
            matches = re.finditer(class_pattern, code)
            
            for match in matches:
                class_name = match.group(1)
                entities.append({
                    "name": class_name,
                    "type": "class",
                    "start": match.start(),
                    "end": match.end()
                })
                
                # Extract inheritance
                if match.group(2):
                    parents = [p.strip() for p in match.group(2).split(',')]
                    for parent in parents:
                        relationships.append({
                            "source": class_name,
                            "target": parent,
                            "type": "inherits_from",
                            "context": f"class {class_name}({parent})"
                        })
            
            # Extract function definitions
            func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            matches = re.finditer(func_pattern, code)
            
            for match in matches:
                entities.append({
                    "name": match.group(1),
                    "type": "function",
                    "start": match.start(),
                    "end": match.end()
                })
        
        return {
            "entities": self._deduplicate_entities(entities),
            "relationships": self._deduplicate_relationships(relationships),
            "language": language
        }