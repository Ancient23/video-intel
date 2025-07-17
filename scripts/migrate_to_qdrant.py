#!/usr/bin/env python3
"""
Migrate from ChromaDB to Qdrant

This script updates the dev-knowledge-base to use Qdrant instead of ChromaDB
"""
import os
import shutil
from pathlib import Path

def migrate_to_qdrant():
    """Migrate the dev assistant to use Qdrant"""
    
    base_dir = Path(__file__).parent.parent
    rag_dir = base_dir / "dev-knowledge-base" / "rag"
    
    # Backup original dev_assistant.py
    original = rag_dir / "dev_assistant.py"
    backup = rag_dir / "dev_assistant_chromadb_backup.py"
    
    if original.exists() and not backup.exists():
        shutil.copy2(original, backup)
        print(f"✅ Backed up original to {backup}")
    
    # Copy new Qdrant version
    qdrant_version = rag_dir / "dev_assistant_qdrant.py"
    if qdrant_version.exists():
        shutil.copy2(qdrant_version, original)
        print(f"✅ Updated dev_assistant.py to use Qdrant")
    else:
        print(f"❌ Could not find {qdrant_version}")
        return False
    
    # Update imports in __init__.py if it exists
    init_file = rag_dir / "__init__.py"
    if init_file.exists():
        print(f"✅ Found {init_file}")
    
    print("\n📝 Next steps:")
    print("1. Install required packages:")
    print("   pip install qdrant-client langchain-qdrant")
    print("2. Make sure Qdrant is running:")
    print("   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant")
    print("3. Run population scripts to migrate data")
    
    return True

if __name__ == "__main__":
    success = migrate_to_qdrant()
    exit(0 if success else 1)