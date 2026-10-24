"""Ingestion CLI script."""
import argparse
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.workspace_config import get_docs_dir, load_workspace_config
from app.ingestion.pipeline import ingest_workspace
from app.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest documents into a workspace")
    parser.add_argument("--workspace", "-w", required=True, help="Workspace slug")
    parser.add_argument("--file", "-f", help="Specific file to ingest (optional)")
    
    args = parser.parse_args()
    
    workspace_slug = args.workspace
    
    try:
        # Load workspace config to verify it exists
        config = load_workspace_config(workspace_slug)
        logger.info(f"Ingesting documents for workspace: {config.name}")
        
        if args.file:
            # Ingest specific file
            from app.ingestion.pipeline import ingest_file
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                sys.exit(1)
            
            result = ingest_file(workspace_slug, file_path)
            logger.info(f"Result: {result}")
        else:
            # Ingest all files in workspace docs directory
            results = ingest_workspace(workspace_slug)
            
            if not results:
                logger.warning("No PDF files found to ingest")
                sys.exit(0)
            
            # Summary
            succeeded = sum(1 for r in results if r["status"] == "ready")
            failed = sum(1 for r in results if r["status"] == "failed")
            
            logger.info(f"\nIngestion complete:")
            logger.info(f"  Succeeded: {succeeded}")
            logger.info(f"  Failed: {failed}")
            logger.info(f"  Total: {len(results)}")
            
            if failed > 0:
                logger.warning("\nFailed files:")
                for r in results:
                    if r["status"] == "failed":
                        logger.warning(f"  - {r['filename']}: {r['error']}")
        
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
