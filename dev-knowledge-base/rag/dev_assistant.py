import os
from typing import Optional, Dict, List, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
import re


class DevelopmentAssistant:
    """RAG-powered development assistant"""
    
    def __init__(self):
        # Initialize OpenAI
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4")
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path="./knowledge/chromadb",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collections = {}
    
    def _get_collection(self, name: str) -> chromadb.Collection:
        """Get or cache a collection"""
        if name not in self.collections:
            try:
                self.collections[name] = self.chroma_client.get_collection(name)
            except Exception as e:
                print(f"Warning: Could not get collection {name}: {e}")
                return None
        return self.collections[name]
    
    def query_patterns(self, query: str, category: Optional[str] = None) -> str:
        """Query implementation patterns"""
        
        # Determine which collections to search
        if category:
            collection_names = [category]
        else:
            # Search all relevant collections
            collection_names = [
                "lessons_learned",
                "architectural_decisions", 
                "implementation_guides",
                "api_documentation",
                "known_issues",
                "pdf_knowledge"
            ]
        
        # Search in collections
        all_results = []
        
        for collection_name in collection_names:
            collection = self._get_collection(collection_name)
            if not collection:
                continue
                
            try:
                # Query the collection
                results = collection.query(
                    query_texts=[query],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else 1.0
                        
                        all_results.append({
                            "content": doc,
                            "metadata": metadata,
                            "collection": collection_name,
                            "relevance": 1.0 - distance  # Convert distance to relevance
                        })
            except Exception as e:
                print(f"Error querying collection {collection_name}: {e}")
                continue
        
        # Sort by relevance
        all_results.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Take top results
        top_results = all_results[:10]
        
        # Format results for context
        context_parts = []
        for result in top_results:
            source = result["metadata"].get("source", "Unknown")
            collection = result["collection"]
            content = result["content"]
            
            context_parts.append(f"**Source**: {source} (from {collection})\n{content}\n")
        
        context = "\n---\n".join(context_parts)
        
        # Generate response with context
        prompt = f"""Based on the VideoCommentator project patterns and the new Video Intelligence architecture,
provide guidance for: {query}

Relevant patterns found:
{context}

Consider:
1. Lessons learned from the old implementation
2. New architectural requirements  
3. Best practices identified
4. Known issues and their solutions

Provide a concise, actionable response."""
        
        try:
            response = self.llm.predict(prompt)
            return response
        except Exception as e:
            return f"Error generating response: {e}\n\nContext found:\n{context}"
    
    def suggest_implementation(self, component: str) -> Dict[str, Any]:
        """Suggest implementation based on past patterns"""
        
        # Find similar components
        similar = self._find_similar_components(component)
        
        # Extract patterns
        patterns = self._extract_implementation_patterns(similar)
        
        return {
            "suggested_structure": patterns.get("structure", ["No specific structure found"]),
            "required_patterns": patterns.get("must_have", ["Follow general best practices"]),
            "common_pitfalls": patterns.get("pitfalls", ["No specific pitfalls identified"]),
            "reference_implementations": patterns.get("references", ["Check the old VideoCommentator codebase"])
        }
    
    def _find_similar_components(self, component: str) -> List[Dict]:
        """Find similar components in knowledge base"""
        similar = []
        
        # Search for component patterns
        collections_to_search = ["implementation_guides", "architectural_decisions", "lessons_learned"]
        
        for collection_name in collections_to_search:
            collection = self._get_collection(collection_name)
            if not collection:
                continue
                
            try:
                results = collection.query(
                    query_texts=[f"{component} implementation pattern structure"],
                    n_results=5,
                    include=["documents", "metadatas"]
                )
                
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        
                        similar.append({
                            "content": doc,
                            "metadata": metadata,
                            "collection": collection_name
                        })
            except Exception as e:
                print(f"Error searching for similar components: {e}")
                continue
        
        return similar
    
    def _extract_implementation_patterns(self, similar_components: List[Dict]) -> Dict[str, List[str]]:
        """Extract implementation patterns from similar components"""
        patterns = {
            "structure": [],
            "must_have": [],
            "pitfalls": [],
            "references": []
        }
        
        for component in similar_components:
            content = component["content"]
            metadata = component["metadata"]
            
            # Extract structure patterns
            structure_matches = re.findall(r"(?:structure|class|interface|module):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            patterns["structure"].extend(structure_matches)
            
            # Extract must-have patterns
            must_have_matches = re.findall(r"(?:must|always|require|should):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            patterns["must_have"].extend(must_have_matches)
            
            # Extract pitfalls
            pitfall_matches = re.findall(r"(?:pitfall|avoid|don't|never|issue):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            patterns["pitfalls"].extend(pitfall_matches)
            
            # Add reference
            source = metadata.get("source", "Unknown")
            patterns["references"].append(f"{source} ({component['collection']})")
        
        # Deduplicate
        for key in patterns:
            patterns[key] = list(set(patterns[key]))[:5]  # Keep top 5 unique items
        
        return patterns