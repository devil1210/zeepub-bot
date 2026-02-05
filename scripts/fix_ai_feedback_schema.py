import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.db_manager_pg import pg_manager
from utils.library_db import get_session
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_schema():
    logger.info("Checking and fixing ai_learning_feedback schema...")
    
    with get_session() as session:
        # Check if column proposed_spanish exists
        try:
            # Postgres specific query to check columns
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='ai_learning_feedback' AND column_name='proposed_spanish';
            """)
            result = session.execute(check_query).scalar()
            
            if not result:
                logger.info("Adding missing column 'proposed_spanish'...")
                session.execute(text("ALTER TABLE ai_learning_feedback ADD COLUMN proposed_spanish VARCHAR"))
                session.commit()
            else:
                logger.info("Column 'proposed_spanish' already exists.")

            # Check if column final_spanish exists
            check_query_final = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='ai_learning_feedback' AND column_name='final_spanish';
            """)
            result_final = session.execute(check_query_final).scalar()
            
            if not result_final:
                logger.info("Adding missing column 'final_spanish'...")
                session.execute(text("ALTER TABLE ai_learning_feedback ADD COLUMN final_spanish VARCHAR"))
                session.commit()
            else:
                logger.info("Column 'final_spanish' already exists.")
                
            logger.info("Schema fix completed successfully.")
            
        except Exception as e:
            logger.error(f"Error updating schema: {e}")
            session.rollback()

if __name__ == "__main__":
    fix_schema()
