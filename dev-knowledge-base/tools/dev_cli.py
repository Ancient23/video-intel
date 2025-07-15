import click
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
import asyncio
from typing import Optional, List, Dict
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import our modules
from rag.dev_assistant import DevelopmentAssistant
from ingestion.extract_knowledge import KnowledgeExtractor
import motor.motor_asyncio
from beanie import init_beanie

# Import models from populate_knowledge_base script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from populate_knowledge_base import ProjectKnowledge, ExtractionReport

console = Console()


async def init_mongodb():
    """Initialize MongoDB connection"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
    
    # Initialize Beanie
    await init_beanie(
        database=client.dev_knowledge_base,
        document_models=[ProjectKnowledge, ExtractionReport]
    )
    
    return client


@click.group()
def cli():
    """Development knowledge base CLI"""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


@cli.command()
@click.argument('query')
@click.option('--category', '-c', help='Filter by category (e.g., lessons_learned, api_documentation)')
@click.option('--limit', '-l', default=5, help='Number of results to return')
def ask(query: str, category: Optional[str], limit: int):
    """Query the development knowledge base"""
    console.print(f"\n🔍 Searching for: [bold cyan]{query}[/bold cyan]\n")
    
    try:
        assistant = DevelopmentAssistant()
        response = assistant.query_patterns(query, category)
        
        # Display response in a nice panel
        console.print(Panel(
            Markdown(response),
            title="💡 Knowledge Base Response",
            border_style="cyan"
        ))
    except Exception as e:
        console.print(f"[red]Error querying knowledge base: {e}[/red]")
        console.print("[yellow]Make sure ChromaDB collections are initialized and OpenAI API key is set.[/yellow]")


@cli.command()
@click.argument('component')
def suggest(component: str):
    """Get implementation suggestions for a component"""
    console.print(f"\n🔧 Getting suggestions for: [bold cyan]{component}[/bold cyan]\n")
    
    try:
        assistant = DevelopmentAssistant()
        suggestions = assistant.suggest_implementation(component)
        
        # Display as table
        table = Table(title=f"Implementation Suggestions for {component}", show_header=True)
        table.add_column("Aspect", style="cyan", width=30)
        table.add_column("Details", style="green")
        
        for key, value in suggestions.items():
            if isinstance(value, list):
                value_str = "\n".join(f"• {item}" for item in value)
            elif isinstance(value, dict):
                value_str = "\n".join(f"• {k}: {v}" for k, v in value.items())
            else:
                value_str = str(value)
            
            table.add_row(key.replace("_", " ").title(), value_str)
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error getting suggestions: {e}[/red]")


@cli.command()
def status():
    """Show project implementation status"""
    console.print("\n📊 Project Implementation Status\n")
    
    async def get_status():
        try:
            await init_mongodb()
            
            # Get all project knowledge items
            total_items = await ProjectKnowledge.count()
            
            # Get items by category
            categories = await ProjectKnowledge.distinct("category")
            
            # Get extraction reports
            reports = await ExtractionReport.find_all().to_list()
            latest_report = max(reports, key=lambda r: r.completed_at if r.completed_at else datetime.min) if reports else None
            
            # Display summary table
            table = Table(title="Knowledge Base Status", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Knowledge Items", str(total_items))
            table.add_row("Categories", ", ".join(categories))
            table.add_row("Extraction Runs", str(len(reports)))
            
            if latest_report:
                if latest_report.completed_at:
                    table.add_row("Last Updated", latest_report.completed_at.strftime("%Y-%m-%d %H:%M:%S"))
                
                # Show statistics from latest report
                if latest_report.statistics:
                    stats = latest_report.statistics
                    if "inventory_report" in stats:
                        table.add_row("Documents Processed", str(stats["inventory_report"]["total_documents"]))
                    if "pdf_summary" in stats:
                        table.add_row("PDFs Processed", str(stats["pdf_summary"]["total_pdfs"]))
            
            console.print(table)
            
            # Show category breakdown
            console.print("\n📁 Knowledge by Category:\n")
            
            category_table = Table(show_header=True)
            category_table.add_column("Category", style="cyan")
            category_table.add_column("Count", style="green")
            
            for category in sorted(categories):
                count = await ProjectKnowledge.find(ProjectKnowledge.category == category).count()
                category_table.add_row(category.replace("_", " ").title(), str(count))
            
            console.print(category_table)
            
        except Exception as e:
            console.print(f"[red]Error getting status: {e}[/red]")
            console.print("[yellow]Make sure MongoDB is running: docker compose up -d[/yellow]")
    
    asyncio.run(get_status())


@cli.command()
@click.argument('topic')
@click.option('--output', '-o', help='Output file path (optional)')
def context(topic: str, output: Optional[str]):
    """Generate context for Claude CLI on a specific topic"""
    console.print(f"\n🤖 Generating Claude context for: [bold cyan]{topic}[/bold cyan]\n")
    
    try:
        from tools.generate_claude_context import ClaudeContextGenerator
        
        generator = ClaudeContextGenerator()
        context_text = generator.generate_context(topic)
        
        if output:
            # Save to file
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(context_text)
            console.print(f"✅ Context saved to: [green]{output_path}[/green]")
        else:
            # Display in console
            console.print(Panel(
                Markdown(context_text),
                title=f"Claude Context: {topic}",
                border_style="cyan"
            ))
            
    except Exception as e:
        console.print(f"[red]Error generating context: {e}[/red]")


@cli.command()
@click.option('--category', '-c', help='Filter by category')
@click.option('--search', '-s', help='Search in titles')
def list(category: Optional[str], search: Optional[str]):
    """List all knowledge items in the database"""
    console.print("\n📚 Knowledge Base Contents\n")
    
    async def list_items():
        try:
            await init_mongodb()
            
            # Build query
            query = {}
            if category:
                query["category"] = category
            
            # Get items
            items = await ProjectKnowledge.find(query).to_list()
            
            # Filter by search if provided
            if search:
                search_lower = search.lower()
                items = [item for item in items if search_lower in item.title.lower()]
            
            # Group by category
            by_category = {}
            for item in items:
                if item.category not in by_category:
                    by_category[item.category] = []
                by_category[item.category].append(item)
            
            # Display
            for cat, cat_items in sorted(by_category.items()):
                console.print(f"\n[bold cyan]{cat.replace('_', ' ').title()}[/bold cyan] ({len(cat_items)} items):")
                
                for item in sorted(cat_items, key=lambda x: x.title)[:10]:  # Show first 10
                    importance_color = {5: "red", 4: "yellow", 3: "green", 2: "blue", 1: "white"}
                    color = importance_color.get(item.importance, "white")
                    console.print(f"  [{color}]{'★' * item.importance}[/{color}] {item.title}")
                
                if len(cat_items) > 10:
                    console.print(f"  [dim]... and {len(cat_items) - 10} more[/dim]")
            
            console.print(f"\n[bold]Total items: {len(items)}[/bold]")
            
        except Exception as e:
            console.print(f"[red]Error listing items: {e}[/red]")
    
    asyncio.run(list_items())


@cli.command()
def collections():
    """List ChromaDB collections and their stats"""
    console.print("\n🗄️  ChromaDB Collections\n")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path="./knowledge/chromadb",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get all collections
        collections = client.list_collections()
        
        if not collections:
            console.print("[yellow]No collections found. Run populate_knowledge_base.py first.[/yellow]")
            return
        
        # Display collection info
        table = Table(title="ChromaDB Collections", show_header=True)
        table.add_column("Collection", style="cyan")
        table.add_column("Documents", style="green")
        table.add_column("Description", style="white")
        
        for collection in collections:
            try:
                count = collection.count()
                metadata = collection.metadata or {}
                description = metadata.get("description", "No description")
                
                table.add_row(collection.name, str(count), description)
            except Exception as e:
                table.add_row(collection.name, "Error", str(e))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error accessing ChromaDB: {e}[/red]")


if __name__ == "__main__":
    cli()