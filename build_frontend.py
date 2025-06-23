#!/usr/bin/env python3
"""
Build script for the Voice AI Dashboard frontend integration
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return success status"""
    try:
        print(f"Running: {command}")
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main build function"""
    # Get the current directory (should be the voiceai root)
    root_dir = Path(__file__).parent
    demo_dir = root_dir / "demo"
    
    print("🚀 Building Voice AI Dashboard Frontend...")
    print(f"Root directory: {root_dir}")
    print(f"Frontend directory: {demo_dir}")
    
    # Check if demo directory exists
    if not demo_dir.exists():
        print("❌ Demo directory not found!")
        return False
    
    # Change to demo directory
    os.chdir(demo_dir)
    
    # Check if package.json exists
    if not (demo_dir / "package.json").exists():
        print("❌ package.json not found in demo directory!")
        return False
    
    # Install dependencies
    print("\n📦 Installing frontend dependencies...")
    if not run_command("npm install", cwd=demo_dir):
        print("❌ Failed to install dependencies")
        return False
    
    # Build the frontend
    print("\n🔨 Building frontend for production...")
    if not run_command("npm run build", cwd=demo_dir):
        print("❌ Failed to build frontend")
        return False
    
    # Check if dist directory was created
    dist_dir = demo_dir / "dist"
    if not dist_dir.exists():
        print("❌ Build failed - dist directory not found")
        return False
    
    print(f"\n✅ Frontend built successfully!")
    print(f"📁 Build output: {dist_dir}")
    
    # List build contents
    print("\n📋 Build contents:")
    for item in dist_dir.iterdir():
        size = "dir" if item.is_dir() else f"{item.stat().st_size} bytes"
        print(f"  - {item.name} ({size})")
    
    # Instructions for running the app
    print("\n🎉 Integration Complete!")
    print("\n📝 Next Steps:")
    print("1. Start the Flask backend:")
    print("   python app.py")
    print("\n2. Open your browser to: http://localhost:5000")
    print("\n3. Login with credentials:")
    print("   Username: admin")
    print("   Password: password")
    print("\n4. Your dashboard will show real data from the Flask API!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)