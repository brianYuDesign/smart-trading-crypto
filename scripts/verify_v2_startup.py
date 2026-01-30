
import subprocess
import os
import time
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_startup(mode):
    logger.info(f"Testing startup in {mode} mode...")
    
    env = os.environ.copy()
    env['BOT_MODE'] = mode
    env['PYTHONPATH'] = PROJECT_ROOT
    # Prevent actual flask run from blocking forever if possible, or just kill it
    
    process = subprocess.Popen(
        [sys.executable, 'main.py'],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for a few seconds to see if it crashes immediately
    time.sleep(5)
    
    if process.poll() is not None:
        # Process exited
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(f"❌ {mode} mode failed to start!")
            logger.error(f"Return Code: {process.returncode}")
            logger.error(f"STDERR: {stderr}")
            return False
        else:
            logger.info(f"⚠️ {mode} mode exited unexpectedly (but with 0 code).")
            return True
    else:
        # Process is still running, which is good for a server/monitor
        logger.info(f"✅ {mode} mode started successfully and is running.")
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        return True

if __name__ == "__main__":
    success = True
    
    # Test Webhook Mode
    if not test_startup('webhook'):
        success = False
        
    # Test Monitoring Mode
    # Note: Monitoring mode in main.py currently just logs a message and keeps running or exits depending on implementation.
    # Our implementation: imports dummy modules and logs placeholder.
    if not test_startup('monitoring'):
        success = False # It might fail if dependencies are missing, which we want to know.
        
    if success:
        logger.info("🎉 All startup tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some startup tests failed.")
        sys.exit(1)
