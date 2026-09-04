#!/usr/bin/env python3
"""
Quick Setup Script for Gmail Order Processor
Helps beginners get started with minimal manual steps.
"""

import os
import sys
import subprocess
import platform

def print_header(title):
    """Print a nice header."""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def run_command(command, description):
    """Run a command and show the result."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False

def check_python():
    """Check if Python is installed."""
    print("🔍 Checking Python installation...")
    
    # Try different Python commands
    python_commands = ['python3', 'python']
    
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ Found {version}")
                return cmd
        except FileNotFoundError:
            continue
    
    print("❌ Python not found!")
    print("\nPlease install Python first:")
    print("- Visit: https://www.python.org/downloads/")
    print("- Download and install Python 3.8 or higher")
    if platform.system() == "Windows":
        print("- IMPORTANT: Check 'Add to PATH' during installation")
    return None

def check_virtual_env():
    """Check if virtual environment exists."""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    return False

def create_virtual_env(python_cmd):
    """Create virtual environment."""
    print("🔧 Creating virtual environment...")
    return run_command(f"{python_cmd} -m venv venv", "Virtual environment creation")

def get_activation_command():
    """Get the correct activation command for the platform."""
    if platform.system() == "Windows":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def install_requirements():
    """Install Python requirements."""
    print("🔧 Installing Python packages...")
    
    # Get the correct pip command based on platform
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    return run_command(f"{pip_cmd} install -r requirements.txt", "Package installation")

def check_oauth_setup():
    """Check if OAuth is already set up."""
    if os.path.exists("credentials.json") and os.path.exists("token.json"):
        print("✅ OAuth already configured")
        return True
    elif os.path.exists("credentials.json"):
        print("⚠️ OAuth partially configured (credentials.json found, but no token.json)")
        return False
    else:
        print("❌ OAuth not configured")
        return False

def check_env_file():
    """Check if .env file exists."""
    if os.path.exists(".env"):
        print("✅ Configuration file (.env) exists")
        return True
    else:
        print("❌ Configuration file (.env) not found")
        return False

def copy_env_template():
    """Copy .env.example to .env."""
    try:
        import shutil
        shutil.copy(".env.example", ".env")
        print("✅ Created .env file from template")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {str(e)}")
        return False

def main():
    """Main setup function."""
    print_header("Gmail Order Processor - Quick Setup")
    print("This script will help you set up the Gmail Order Processor")
    print("Follow the prompts and we'll get you running in no time!")
    
    # Step 1: Check Python
    print_header("Step 1: Python Check")
    python_cmd = check_python()
    if not python_cmd:
        print("\n🛑 Setup cannot continue without Python.")
        print("Please install Python and run this script again.")
        sys.exit(1)
    
    # Step 2: Virtual Environment
    print_header("Step 2: Virtual Environment")
    if not check_virtual_env():
        if not create_virtual_env(python_cmd):
            print("🛑 Failed to create virtual environment.")
            sys.exit(1)
    
    # Step 3: Install Requirements
    print_header("Step 3: Python Packages")
    if not install_requirements():
        print("🛑 Failed to install required packages.")
        print("Try running this manually:")
        activation_cmd = get_activation_command()
        print(f"  {activation_cmd}")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Step 4: Configuration File
    print_header("Step 4: Configuration File")
    if not check_env_file():
        if copy_env_template():
            print("\n📝 IMPORTANT: You need to edit the .env file with your inFlow API credentials!")
            print("Edit these lines in .env:")
            print("  INFLOW_API_KEY=your-actual-api-key")
            print("  INFLOW_COMPANY_ID=your-actual-company-id")
        else:
            print("🛑 Failed to create configuration file.")
            sys.exit(1)
    
    # Step 5: OAuth Setup
    print_header("Step 5: Gmail OAuth Setup")
    if not check_oauth_setup():
        print("\n🔐 You need to set up Gmail authentication.")
        print("This will open your web browser to sign in to Gmail.")
        
        response = input("\nRun Gmail OAuth setup now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            activation_cmd = get_activation_command()
            if platform.system() == "Windows":
                python_path = "venv\\Scripts\\python"
            else:
                python_path = "venv/bin/python"
            
            print("🔧 Starting OAuth setup...")
            try:
                subprocess.run([python_path, "setup_oauth_flow.py"])
                print("✅ OAuth setup completed!")
            except Exception as e:
                print(f"❌ OAuth setup failed: {str(e)}")
                print("You can run it manually later:")
                print(f"  {activation_cmd}")
                print("  python setup_oauth_flow.py")
        else:
            print("⚠️ OAuth setup skipped. Run it manually when ready:")
            activation_cmd = get_activation_command()
            print(f"  {activation_cmd}")
            print("  python setup_oauth_flow.py")
    
    # Final Instructions
    print_header("Setup Complete!")
    print("🎉 Great! Your Gmail Order Processor is ready.")
    print("\n📋 To run the order processor:")
    activation_cmd = get_activation_command()
    print(f"  {activation_cmd}")
    print("  python main.py")
    
    print("\n📖 For detailed instructions, see:")
    print("  - README.md (overview)")
    print("  - INSTALL.md (step-by-step guide)")
    
    print("\n🔧 Remember to:")
    print("  1. Edit .env with your inFlow API credentials")
    print("  2. Complete OAuth setup if not done")
    print("  3. Run 'python main.py' to start monitoring")
    
    print("\n✨ Happy order processing!")

if __name__ == "__main__":
    main()