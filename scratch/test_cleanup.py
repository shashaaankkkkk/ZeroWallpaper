import os
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from zerowallpaper.core.config import AppConfig
from zerowallpaper.core.cache import CacheManager

def test_cleanup():
    config = AppConfig()
    cache = CacheManager(config)
    
    # Create a fake old file in thumbnails
    old_file = config.thumbnails_dir / "test_old.png"
    old_file.write_bytes(b"old")
    
    # Set its mtime to 10 days ago
    past_time = time.time() - (10 * 86400)
    os.utime(old_file, (past_time, past_time))
    
    # Create a fake new file
    new_file = config.thumbnails_dir / "test_new.png"
    new_file.write_bytes(b"new")
    
    print(f"Before cleanup: {old_file.exists()=}, {new_file.exists()=}")
    
    deleted = cache.cleanup(max_age_days=7)
    print(f"Deleted {deleted} files")
    
    print(f"After cleanup: {old_file.exists()=}, {new_file.exists()=}")
    
    if not old_file.exists() and new_file.exists():
        print("SUCCESS: Old file deleted, new file kept.")
    else:
        print("FAILURE: Cleanup logic failed.")
    
    # Final cleanup
    if new_file.exists():
        new_file.unlink()

if __name__ == "__main__":
    test_cleanup()
