from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ai-agent",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ai-agent=services.cli_service:main",
        ],
    },
    install_requires=requirements,
    author="Tim Wijma",
    description="Simple AI Agent",
    python=">=3.10.12",
    package_data={
        "prompts": ["*.txt"]
    },
    include_package_data=True,
)