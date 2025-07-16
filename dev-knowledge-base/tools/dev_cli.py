import click
import os
import sys
import builtins
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
import motor.motor_asyncio
from beanie import init_beanie

# Import models
from models import ProjectKnowledge, ExtractionReport

# Lazy imports to avoid initialization issues
DevelopmentAssistant = None
KnowledgeExtractor = None

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
@click.option('--debug', is_flag=True, help='Enable debug output')
@click.pass_context
def cli(ctx, debug):
    """Development knowledge base CLI
    
    A unified tool for managing development knowledge, prompts, and project status.
    
    Key commands:
      ask      - Query development patterns and knowledge
      status   - Check project implementation progress
      suggest  - Get implementation recommendations
      
    Note: For prompt execution, use: python scripts/prompt.py
    """
    # Store debug flag in context
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        if debug:
            console.print("[dim]Loaded environment from .env[/dim]")


@cli.command()
@click.argument('query')
@click.option('--category', '-c', help='Filter by category (e.g., lessons_learned, api_documentation)')
@click.option('--limit', '-l', default=5, help='Number of results to return')
@click.pass_context
def ask(ctx, query: str, category: Optional[str], limit: int):
    """Query the development knowledge base"""
    console.print(f"\n🔍 Searching for: [bold cyan]{query}[/bold cyan]\n")
    
    debug = ctx.obj.get('debug', False)
    
    try:
        # Lazy import
        global DevelopmentAssistant
        if DevelopmentAssistant is None:
            from rag.dev_assistant import DevelopmentAssistant
        
        if debug:
            console.print("[dim]Initializing DevelopmentAssistant...[/dim]")
        
        assistant = DevelopmentAssistant(debug=debug)
        response = assistant.query_patterns(query, category)
        
        # Display response in a nice panel
        console.print(Panel(
            Markdown(response),
            title="💡 Knowledge Base Response",
            border_style="cyan"
        ))
    except TimeoutError as e:
        console.print(f"[red]Operation timed out: {e}[/red]")
        console.print("[yellow]Tips:[/yellow]")
        console.print("  • Check if ChromaDB is running: docker compose ps")
        console.print("  • Verify OpenAI API key is set in .env")
        console.print("  • Try running with --debug flag for more details")
    except ConnectionError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        console.print("[yellow]Make sure all services are running:[/yellow]")
        console.print("  • docker compose up -d")
    except Exception as e:
        console.print(f"[red]Error querying knowledge base: {e}[/red]")
        if debug:
            import traceback
            console.print("[dim]Full traceback:[/dim]")
            traceback.print_exc()


@cli.command()
@click.argument('component')
@click.pass_context
def suggest(ctx, component: str):
    """Get implementation suggestions for a component"""
    console.print(f"\n🔧 Getting suggestions for: [bold cyan]{component}[/bold cyan]\n")
    
    debug = ctx.obj.get('debug', False)
    
    try:
        # Lazy import
        global DevelopmentAssistant
        if DevelopmentAssistant is None:
            from rag.dev_assistant import DevelopmentAssistant
        
        if debug:
            console.print("[dim]Initializing DevelopmentAssistant...[/dim]")
        
        assistant = DevelopmentAssistant(debug=debug)
        suggestions = assistant.suggest_implementation(component)
        
        # Display as table
        table = Table(title=f"Implementation Suggestions for {component}", show_header=True)
        table.add_column("Aspect", style="cyan", width=30)
        table.add_column("Details", style="green")
        
        for key, value in suggestions.items():
            # Debug: check what 'list' is at this point
            # console.print(f"[yellow]Debug: list is {list}, type is {type(list)}[/yellow]")
            # console.print(f"[yellow]Debug: value is {value}, type is {type(value)}[/yellow]")
            if isinstance(value, builtins.list):
                value_str = "\n".join(f"• {item}" for item in value)
            elif isinstance(value, builtins.dict):
                value_str = "\n".join(f"• {k}: {v}" for k, v in value.items())
            else:
                value_str = str(value)
            
            table.add_row(key.replace("_", " ").title(), value_str)
        
        console.print(table)
    except TimeoutError as e:
        console.print(f"[red]Operation timed out: {e}[/red]")
        console.print("[yellow]Tips:[/yellow]")
        console.print("  • Check if services are running: docker compose ps")
        console.print("  • Try running with --debug flag for more details")
    except ConnectionError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        console.print("[yellow]Make sure all services are running:[/yellow]")
        console.print("  • docker compose up -d")
    except Exception as e:
        console.print(f"[red]Error getting suggestions: {e}[/red]")
        if debug:
            import traceback
            console.print("[dim]Full traceback:[/dim]")
            traceback.print_exc()


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
@click.pass_context
def context(ctx, topic: str, output: Optional[str]):
    """Generate context for Claude CLI on a specific topic"""
    console.print(f"\n🤖 Generating Claude context for: [bold cyan]{topic}[/bold cyan]\n")
    
    debug = ctx.obj.get('debug', False)
    
    try:
        # Dynamic import to avoid initialization issues
        from tools.generate_claude_context import ClaudeContextGenerator
        
        if debug:
            console.print("[dim]Initializing ClaudeContextGenerator...[/dim]")
        
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
            
    except TimeoutError as e:
        console.print(f"[red]Operation timed out: {e}[/red]")
        console.print("[yellow]Tips:[/yellow]")
        console.print("  • Check if services are running: docker compose ps")
        console.print("  • Try running with --debug flag for more details")
    except ConnectionError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        console.print("[yellow]Make sure all services are running:[/yellow]")
        console.print("  • docker compose up -d")
    except Exception as e:
        console.print(f"[red]Error generating context: {e}[/red]")
        if debug:
            import traceback
            console.print("[dim]Full traceback:[/dim]")
            traceback.print_exc()


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
        
        # Check environment for ChromaDB client type
        chroma_type = os.getenv("CHROMA_CLIENT_TYPE", "persistent")
        
        if chroma_type == "http":
            # Use HTTP client to connect to Docker ChromaDB
            client = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST", "localhost"),
                port=int(os.getenv("CHROMA_PORT", "8000")),
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
        else:
            # Use persistent client for local development
            client = chromadb.PersistentClient(
                path=os.getenv("CHROMA_PERSIST_PATH", "./knowledge/chromadb"),
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
        console.print("[yellow]Check CHROMA_CLIENT_TYPE in .env (use 'persistent' for local or 'http' for Docker)[/yellow]")




if __name__ == "__main__":
    cli()