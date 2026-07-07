# check_requirements.py
"""Quick check if all requirements are installed"""

import sys
import importlib.metadata

# Your requirements from requirements.txt
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "python-dotenv",
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "alembic",
    "psycopg2",
    "asyncpg",
    "python-jose",
    "passlib",
    "python-multipart",
    "oauthlib",
    "requests-oauthlib",
    "langchain",
    "langchain-groq",
    "langgraph",
    "langsmith",
    "PyGithub",
    "gitpython",
    "celery",
    "redis",
    "docker",
    "httpx",
    "aiofiles",
    "python-dateutil",
    "chardet",
    "pyyaml",
    "jinja2",
    "markdown",
    "weasyprint",
    "pdfkit",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
]

def check_all():
    print("\n" + "="*60)
    print("📦 CHECKING INSTALLED PACKAGES")
    print("="*60 + "\n")
    
    missing = []
    installed = []
    
    for pkg in REQUIRED_PACKAGES:
        try:
            version = importlib.metadata.version(pkg)
            installed.append((pkg, version))
            print(f"✅ {pkg:<25} {version}")
        except importlib.metadata.PackageNotFoundError:
            missing.append(pkg)
            print(f"❌ {pkg:<25} NOT INSTALLED")
    
    print("\n" + "="*60)
    print(f"📊 Installed: {len(installed)}/{len(REQUIRED_PACKAGES)}")
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n🔧 Install missing packages with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    else:
        print("\n✅ All packages are installed correctly!")
        return True

if __name__ == "__main__":
    sys.exit(0 if check_all() else 1)