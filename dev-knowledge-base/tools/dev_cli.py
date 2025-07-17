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
        
        # Display response in a nice panel
        console.print(Panel(
            Markdown(suggestions),
            title=f"💡 Implementation Suggestions for {component}",
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
def info():
    """Display information about the knowledge base"""
    console.print("\n🔍 Knowledge Base Information\n")
    
    try:
        # Lazy import
        global DevelopmentAssistant
        if DevelopmentAssistant is None:
            from rag.dev_assistant import DevelopmentAssistant
        
        assistant = DevelopmentAssistant()
        stats = assistant.get_statistics()
        
        # Display statistics
        table = Table(title="Knowledge Base Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Documents", str(stats.get('total_documents', 0)))
        table.add_row("Vector Size", str(stats.get('vector_size', 1536)))
        table.add_row("Distance Metric", stats.get('distance_metric', 'cosine'))
        table.add_row("Status", stats.get('status', 'unknown'))
        
        if 'error' in stats:
            table.add_row("Error", f"[red]{stats['error']}[/red]")
        
        console.print(table)
        
        # Check Graph-RAG availability
        try:
            from rag.graph_rag_assistant import GraphRAGAssistant
            graph_assistant = GraphRAGAssistant()
            graph_stats = graph_assistant.get_statistics()
            
            console.print("\n")
            graph_table = Table(title="Graph-RAG Statistics", show_header=True)
            graph_table.add_column("Component", style="cyan")
            graph_table.add_column("Status", style="green")
            
            # Vector DB stats
            if "vector_db" in graph_stats:
                vdb = graph_stats["vector_db"]
                if "error" not in vdb:
                    graph_table.add_row("Qdrant", f"✅ {vdb.get('total_points', 0)} points")
                else:
                    graph_table.add_row("Qdrant", f"❌ {vdb['error']}")
            
            # Graph DB stats
            if "graph_db" in graph_stats:
                gdb = graph_stats["graph_db"]
                if "error" not in gdb:
                    nodes = gdb.get('node_count', 0)
                    entities = gdb.get('entity_count', 0)
                    rels = gdb.get('relationship_count', 0)
                    graph_table.add_row("Neo4j", f"✅ {nodes} nodes, {entities} entities, {rels} relationships")
                else:
                    graph_table.add_row("Neo4j", f"❌ {gdb.get('error', 'Not connected')}")
            
            console.print(graph_table)
            
        except Exception as e:
            console.print("\n[yellow]Graph-RAG not available[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error accessing knowledge base: {e}[/red]")
        console.print("[yellow]Make sure Qdrant is running: docker compose up -d[/yellow]")


@cli.command()
@click.argument('query')
@click.option('--graph/--no-graph', default=True, help='Use Graph-RAG enhancement')
@click.option('--limit', '-l', default=5, help='Number of results')
@click.pass_context
def search(ctx, query: str, graph: bool, limit: int):
    """Advanced search with Graph-RAG capabilities"""
    console.print(f"\n🔍 Searching with Graph-RAG: [bold cyan]{query}[/bold cyan]\n")
    
    debug = ctx.obj.get('debug', False)
    
    try:
        # Use Graph-RAG if available and requested
        if graph:
            try:
                from rag.graph_rag_assistant import GraphRAGAssistant
                assistant = GraphRAGAssistant(debug=debug)
                response = assistant.ask(query, context_limit=limit, use_graph=True)
                
                console.print(Panel(
                    Markdown(response),
                    title="💡 Graph-RAG Response",
                    border_style="green"
                ))
                return
            except ImportError:
                console.print("[yellow]Graph-RAG not available, falling back to standard search[/yellow]\n")
        
        # Fallback to standard assistant
        global DevelopmentAssistant
        if DevelopmentAssistant is None:
            from rag.dev_assistant import DevelopmentAssistant
        
        assistant = DevelopmentAssistant(debug=debug)
        response = assistant.ask(query, context_limit=limit)
        
        console.print(Panel(
            Markdown(response),
            title="💡 Knowledge Base Response",
            border_style="cyan"
        ))
        
    except Exception as e:
        console.print(f"[red]Error performing search: {e}[/red]")
        if debug:
            import traceback
            traceback.print_exc()


@cli.command()
@click.argument('entity')
@click.option('--depth', '-d', default=2, help='Maximum relationship depth')
@click.pass_context
def explore(ctx, entity: str, depth: int):
    """Explore entity relationships in the knowledge graph"""
    console.print(f"\n🕸️  Exploring relationships for: [bold cyan]{entity}[/bold cyan]\n")
    
    debug = ctx.obj.get('debug', False)
    
    try:
        from rag.graph_rag_assistant import GraphRAGAssistant
        
        assistant = GraphRAGAssistant(debug=debug)
        graph = assistant.explore_relationships(entity, max_depth=depth)
        
        if "error" in graph:
            console.print(f"[red]Error: {graph['error']}[/red]")
            return
        
        # Display graph structure
        console.print(f"Entity: [bold]{graph['entity']}[/bold]\n")
        
        if not graph['connections']:
            console.print("[yellow]No relationships found.[/yellow]")
            return
        
        # Group by depth
        by_depth = {}
        for conn in graph['connections']:
            d = conn['depth']
            if d not in by_depth:
                by_depth[d] = []
            by_depth[d].append(conn)
        
        # Display by depth
        for d in sorted(by_depth.keys()):
            console.print(f"\n[cyan]Depth {d}:[/cyan]")
            
            table = Table(show_header=True)
            table.add_column("Type", style="green")
            table.add_column("Name", style="white")
            table.add_column("Relationships", style="cyan")
            
            for conn in by_depth[d]:
                rel_str = " → ".join(conn['relationships'])
                table.add_row(conn['type'], conn['name'], rel_str)
            
            console.print(table)
            
    except ImportError:
        console.print("[red]Graph-RAG is not available. Make sure Neo4j is running.[/red]")
    except Exception as e:
        console.print(f"[red]Error exploring relationships: {e}[/red]")
        if debug:
            import traceback
            traceback.print_exc()




if __name__ == "__main__":
    cli()