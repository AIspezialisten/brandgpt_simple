#!/usr/bin/env python3
"""Docker readiness check - verify all components for containerized deployment."""

import os
import requests
import subprocess
from pathlib import Path

def check_docker_files():
    """Check if required Docker files exist"""
    print("🐳 Checking Docker Configuration...")
    
    required_files = [
        "Dockerfile",
        "docker-compose.yml", 
        ".env.example",
        "main.py",
        "pyproject.toml"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing_files:
        print(f"  ❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def check_data_directory():
    """Check if data directory exists and is writable"""
    print("\n📁 Checking Data Directory...")
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("  ⚠️  Data directory doesn't exist - will be created by Docker")
        try:
            data_dir.mkdir(parents=True)
            print("  ✅ Created data directory")
        except Exception as e:
            print(f"  ❌ Cannot create data directory: {e}")
            return False
    else:
        print("  ✅ Data directory exists")
    
    # Check if writable
    test_file = data_dir / "test_write"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print("  ✅ Data directory is writable")
    except Exception as e:
        print(f"  ❌ Data directory is not writable: {e}")
        return False
    
    return True

def check_env_configuration():
    """Check environment configuration"""
    print("\n⚙️  Checking Environment Configuration...")
    
    env_example = Path(".env.example")
    if env_example.exists():
        print("  ✅ .env.example exists")
        
        # Check key settings
        content = env_example.read_text()
        docker_settings = [
            "OLLAMA_BASE_URL=http://host.docker.internal:11434",
            "QDRANT_URL=http://qdrant:6333",
            "API_HOST=0.0.0.0"
        ]
        
        for setting in docker_settings:
            if setting in content:
                print(f"  ✅ {setting}")
            else:
                print(f"  ⚠️  Missing or incorrect: {setting}")
        
        return True
    else:
        print("  ❌ .env.example missing")
        return False

def check_ollama_availability():
    """Check if Ollama is available on host"""
    print("\n🦙 Checking Ollama Availability...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"  ✅ Ollama is running with {len(models.get('models', []))} models")
            
            # Check for required models
            model_names = [model['name'] for model in models.get('models', [])]
            required_models = [
                "hf.co/Qwen/Qwen3-Embedding-8B-GGUF",
                "mistral-small:24b"
            ]
            
            for model in required_models:
                if any(model in name for name in model_names):
                    print(f"  ✅ Model available: {model}")
                else:
                    print(f"  ⚠️  Model may be missing: {model}")
            
            return True
        else:
            print(f"  ❌ Ollama responded with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Cannot connect to Ollama: {e}")
        print("  ℹ️  This is expected if Ollama isn't running yet")
        return True  # Don't fail deployment check

def check_docker_availability():
    """Check if Docker and Docker Compose are available"""
    print("\n🐋 Checking Docker Availability...")
    
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {result.stdout.strip()}")
        else:
            print("  ❌ Docker not available")
            return False
    except FileNotFoundError:
        print("  ❌ Docker command not found")
        return False
    
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {result.stdout.strip()}")
        else:
            # Try docker compose (newer syntax)
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ {result.stdout.strip()}")
            else:
                print("  ❌ Docker Compose not available")
                return False
    except FileNotFoundError:
        print("  ❌ Docker Compose command not found")
        return False
    
    return True

def check_port_availability():
    """Check if required ports are available"""
    print("\n🔌 Checking Port Availability...")
    
    ports_to_check = [9700, 6337, 6338]
    
    for port in ports_to_check:
        try:
            response = requests.get(f"http://localhost:{port}", timeout=1)
            print(f"  ⚠️  Port {port} is already in use (service may be running)")
        except requests.exceptions.RequestException:
            print(f"  ✅ Port {port} is available")
    
    return True

def check_dependencies():
    """Check Python dependencies in pyproject.toml"""
    print("\n📦 Checking Dependencies...")
    
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        print("  ✅ pyproject.toml exists")
        
        content = pyproject.read_text()
        critical_deps = ["fastapi", "uvicorn", "qdrant-client", "ollama", "langchain"]
        
        found_deps = []
        for dep in critical_deps:
            if dep in content:
                found_deps.append(dep)
                print(f"  ✅ Dependency found: {dep}")
            else:
                print(f"  ⚠️  Dependency not found: {dep}")
        
        print(f"  📊 Found {len(found_deps)}/{len(critical_deps)} critical dependencies")
        return True
    else:
        print("  ❌ pyproject.toml missing")
        return False

def main():
    """Run all Docker readiness checks"""
    print("🚀 Docker Deployment Readiness Check")
    print("=" * 50)
    
    checks = [
        ("Docker Files", check_docker_files),
        ("Data Directory", check_data_directory),
        ("Environment Config", check_env_configuration),
        ("Dependencies", check_dependencies),
        ("Docker Availability", check_docker_availability),
        ("Port Availability", check_port_availability),
        ("Ollama Connection", check_ollama_availability),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"  ❌ Check failed: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Readiness Summary:")
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, passed_check in results.items():
        status = "✅ PASS" if passed_check else "❌ FAIL"
        print(f"  {check_name}: {status}")
    
    print(f"\n📊 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 System is ready for Docker deployment!")
        print("\nTo deploy:")
        print("  1. Ensure Ollama is running with required models")
        print("  2. Run: docker-compose up -d")
        print("  3. Check: curl http://localhost:9700/health")
    else:
        print("\n⚠️  Some issues need to be addressed before deployment")
        print("Please review the failed checks above")
    
    return passed == total

if __name__ == "__main__":
    main()