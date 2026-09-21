import click
import uvicorn

@click.group()
def main():
    """Sol — Open-Source Autonomous Coding Engine"""
    pass

@main.command()
@click.option("--host", default="127.0.0.1", help="Host address to bind server.")
@click.option("--port", default=8000, help="Port to run backend API.")
def studio(host: str, port: int):
    """Launch the Sol Studio web UI and agent server."""
    click.echo(f"🚀 Launching Sol Studio at http://{host}:{port}")
    uvicorn.run("sol.server:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()
