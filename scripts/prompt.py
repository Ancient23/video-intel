#!/usr/bin/env python3
"""
Prompt Loader Script - Load and execute prompts for AI assistants
"""
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Base directory for prompts
PROMPTS_DIR = Path(__file__).parent.parent / ".claude" / "prompts"

# Prompt metadata
PROMPT_METADATA = {
    # Project Management
    "status-check": {
        "file": "project-management/status-check.md",
        "description": "Check current project status",
        "category": "project-management"
    },
    "status-update": {
        "file": "project-management/status-update.md",
        "description": "Update project status after work",
        "category": "project-management"
    },
    "next-task": {
        "file": "project-management/next-task.md",
        "description": "Get next implementation task",
        "category": "project-management"
    },
    
    # Technical Debt
    "debt-check": {
        "file": "technical-debt/debt-check.md",
        "description": "Review technical debt status",
        "category": "technical-debt"
    },
    "debt-add": {
        "file": "technical-debt/debt-add.md",
        "description": "Add new technical debt item",
        "category": "technical-debt"
    },
    "debt-resolve": {
        "file": "technical-debt/debt-resolve.md",
        "description": "Resolve technical debt item",
        "category": "technical-debt"
    },
    
    # Development
    "impl-plan": {
        "file": "development/impl-plan.md",
        "description": "Plan implementation approach",
        "category": "development"
    },
    "impl-multi": {
        "file": "development/impl-multi.md",
        "description": "Multi-component implementation",
        "category": "development"
    },
    "feature": {
        "file": "development/feature.md",
        "description": "Implement new feature",
        "category": "development"
    },
    "feature-provider": {
        "file": "development/feature-provider.md",
        "description": "Add provider integration",
        "category": "development"
    },
    "bug": {
        "file": "development/bug.md",
        "description": "Investigate and fix bug",
        "category": "development"
    },
    "test": {
        "file": "development/test.md",
        "description": "Add test coverage",
        "category": "development"
    },
    "doc-sync": {
        "file": "development/doc-sync.md",
        "description": "Sync documentation",
        "category": "development"
    },
    
    # Knowledge Base
    "knowledge-query": {
        "file": "knowledge-base/knowledge-query.md",
        "description": "Query development patterns",
        "category": "knowledge-base"
    },
    "knowledge-add": {
        "file": "knowledge-base/knowledge-add.md",
        "description": "Add new knowledge",
        "category": "knowledge-base"
    },
    
    # Workflows
    "common-workflows": {
        "file": "workflows/common-workflows.md",
        "description": "Multi-step development workflows",
        "category": "workflows"
    },
    
    # Architecture
    "arch-decision": {
        "file": "architecture/arch-decision.md",
        "description": "Architecture decision template",
        "category": "architecture"
    },
    "schema-update": {
        "file": "architecture/schema-update.md",
        "description": "MongoDB schema updates",
        "category": "architecture"
    },
    
    # Infrastructure
    "local-setup": {
        "file": "infrastructure/local-setup.md",
        "description": "Local development setup",
        "category": "infrastructure"
    },
    "deploy-prep": {
        "file": "infrastructure/deploy-prep.md",
        "description": "Production deployment prep",
        "category": "infrastructure"
    }
}


class PromptLoader:
    """Load and manage AI assistant prompts"""
    
    def __init__(self):
        self.prompts_dir = PROMPTS_DIR
        self.metadata = PROMPT_METADATA
        
    def list_prompts(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """List available prompts, optionally filtered by category"""
        prompts = []
        
        for name, info in self.metadata.items():
            if category and info["category"] != category:
                continue
                
            prompts.append({
                "name": name,
                "category": info["category"],
                "description": info["description"],
                "file": str(self.prompts_dir / info["file"])
            })
            
        return sorted(prompts, key=lambda x: (x["category"], x["name"]))
    
    def get_prompt(self, name: str) -> Optional[str]:
        """Get prompt content by name"""
        if name not in self.metadata:
            return None
            
        prompt_file = self.prompts_dir / self.metadata[name]["file"]
        
        if not prompt_file.exists():
            return None
            
        with open(prompt_file, 'r') as f:
            return f.read()
    
    def show_prompt(self, name: str) -> None:
        """Display prompt content"""
        content = self.get_prompt(name)
        
        if not content:
            print(f"❌ Prompt '{name}' not found")
            self.suggest_similar(name)
            return
            
        print(content)
    
    def execute_prompt(self, name: str) -> None:
        """Execute commands from a prompt"""
        content = self.get_prompt(name)
        
        if not content:
            print(f"❌ Prompt '{name}' not found")
            self.suggest_similar(name)
            return
        
        print(f"🚀 Executing prompt: {name}")
        print(f"📋 {self.metadata[name]['description']}\n")
        
        # Extract and execute bash commands
        lines = content.split('\n')
        in_code_block = False
        commands = []
        
        for line in lines:
            if line.strip().startswith('```bash'):
                in_code_block = True
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                continue
            elif in_code_block:
                # Skip comments and empty lines
                if line.strip() and not line.strip().startswith('#'):
                    commands.append(line.strip())
        
        if not commands:
            print("ℹ️  No executable commands found in this prompt")
            print("💡 This prompt provides guidance rather than commands")
            return
        
        print(f"Found {len(commands)} commands to execute:\n")
        for i, cmd in enumerate(commands, 1):
            print(f"{i}. {cmd}")
        
        response = input("\nExecute these commands? (y/n): ")
        if response.lower() != 'y':
            print("❌ Execution cancelled")
            return
        
        # Execute commands
        for cmd in commands:
            print(f"\n▶️  Executing: {cmd}")
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Success")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print(f"❌ Failed with code {result.returncode}")
                    if result.stderr:
                        print(result.stderr)
                    
                    response = input("\nContinue with remaining commands? (y/n): ")
                    if response.lower() != 'y':
                        break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
    
    def suggest_similar(self, name: str) -> None:
        """Suggest similar prompt names"""
        suggestions = []
        
        for prompt_name in self.metadata.keys():
            if name.lower() in prompt_name.lower() or prompt_name.lower() in name.lower():
                suggestions.append(prompt_name)
        
        if suggestions:
            print("\n💡 Did you mean:")
            for s in suggestions:
                print(f"   - {s}")
    
    def export_json(self) -> str:
        """Export prompts as JSON for AI consumption"""
        export_data = {
            "prompts": {},
            "categories": {}
        }
        
        # Group by category
        for name, info in self.metadata.items():
            category = info["category"]
            if category not in export_data["categories"]:
                export_data["categories"][category] = []
            
            export_data["categories"][category].append(name)
            
            # Include prompt content
            content = self.get_prompt(name)
            export_data["prompts"][name] = {
                "description": info["description"],
                "category": category,
                "content": content
            }
        
        return json.dumps(export_data, indent=2)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Video Intelligence Prompt Loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/prompt.py list                    # List all prompts
  python scripts/prompt.py list --category dev     # List development prompts
  python scripts/prompt.py show status-check       # Display prompt
  python scripts/prompt.py exec status-check       # Execute prompt
  python scripts/prompt.py help                    # Show this help
  python scripts/prompt.py export                  # Export as JSON
        """
    )
    
    parser.add_argument(
        'action',
        choices=['list', 'show', 'exec', 'execute', 'help', 'export'],
        help='Action to perform'
    )
    
    parser.add_argument(
        'prompt_name',
        nargs='?',
        help='Name of the prompt (for show/exec actions)'
    )
    
    parser.add_argument(
        '--category',
        '-c',
        help='Filter by category (for list action)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    args = parser.parse_args()
    
    loader = PromptLoader()
    
    if args.action == 'help':
        parser.print_help()
        
    elif args.action == 'list':
        prompts = loader.list_prompts(args.category)
        
        if args.json:
            print(json.dumps(prompts, indent=2))
        else:
            if args.category:
                print(f"\n📚 Available prompts in '{args.category}':\n")
            else:
                print("\n📚 Available prompts:\n")
            
            current_category = None
            for prompt in prompts:
                if prompt['category'] != current_category:
                    current_category = prompt['category']
                    print(f"\n{current_category.upper().replace('-', ' ')}")
                    print("-" * len(current_category) * 2)
                
                print(f"  {prompt['name']:<20} - {prompt['description']}")
            
            print(f"\n💡 Use 'python scripts/prompt.py show <name>' to view a prompt")
            print(f"🚀 Use 'python scripts/prompt.py exec <name>' to execute a prompt\n")
    
    elif args.action in ['show', 'exec', 'execute']:
        if not args.prompt_name:
            print("❌ Please specify a prompt name")
            print("💡 Use 'python scripts/prompt.py list' to see available prompts")
            sys.exit(1)
        
        if args.action == 'show':
            loader.show_prompt(args.prompt_name)
        else:
            loader.execute_prompt(args.prompt_name)
    
    elif args.action == 'export':
        print(loader.export_json())


if __name__ == "__main__":
    main()