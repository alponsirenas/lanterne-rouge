#!/usr/bin/env python3
"""
Test Fiction Mode locally
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_fiction_mode():
    """Test fiction mode with the latest stage completion"""
    
    print("🎭 Testing Fiction Mode...")
    
    # Check if we have the required environment variables
    required_env = ['STRAVA_CLIENT_ID', 'STRAVA_CLIENT_SECRET', 'STRAVA_REFRESH_TOKEN', 'OPENAI_API_KEY']
    missing = [var for var in required_env if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("   Please set these in your environment or .env file")
        return 1
    
    # Import and run fiction mode
    from scripts.run_fiction_mode import run_fiction_mode
    
    print("📚 Running with Krabbé style (Tim Krabbé - The Rider)...")
    result = run_fiction_mode(
        activity_id=None,  # Auto-detect
        stage_number=None,  # Auto-detect 
        style='krabbe',
        format='markdown',
        preview_only=False
    )
    
    if result == 0:
        print("\n✅ Fiction mode test completed successfully!")
        
        # Check if output files were created
        fiction_dir = Path("output/fiction_mode")
        if fiction_dir.exists():
            files = list(fiction_dir.glob("*.md"))
            if files:
                print(f"📄 Generated files: {len(files)}")
                for file in files[:3]:  # Show first 3
                    print(f"   - {file.name}")
            else:
                print("⚠️  No markdown files found in output/fiction_mode/")
        else:
            print("⚠️  output/fiction_mode/ directory not created")
    else:
        print("\n❌ Fiction mode test failed")
    
    return result

if __name__ == "__main__":
    sys.exit(test_fiction_mode())
