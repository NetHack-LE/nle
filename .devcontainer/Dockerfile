FROM python:3.12-slim

# Install essential packages 
RUN apt-get update && apt-get install -yq \
    apt-transport-https \
    bash-completion \
    bison \
    build-essential \
    curl \
    flex \
    git \
    libbz2-dev \
    ninja-build \
    sudo \
    vim

# Create non-root user
RUN useradd -m -s /bin/bash vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && mkdir -p /workspace \
    && chown vscode:vscode /workspace \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Switch to non-root user
USER vscode

# Set up uv and Python environment
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up environment variables
ENV PATH="/home/vscode/.local/bin:${PATH}"
