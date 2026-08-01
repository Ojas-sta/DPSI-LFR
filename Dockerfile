FROM python:3.9-slim

# Install system dependencies for OpenCV and lgpio
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    swig \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install lgpio from source (since pre-built packages might be missing for some Debian slim variants)
RUN apt-get update && apt-get install -y wget unzip && \
    wget https://github.com/joan2937/lg/archive/master.zip && \
    unzip master.zip && \
    cd lg-master && \
    make && \
    make install && \
    cd .. && rm -rf lg-master master.zip && \
    apt-get purge -y wget unzip && \
    apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ ./src/
COPY config/ ./config/

CMD ["python", "src/main.py"]
