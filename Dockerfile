FROM python:3.11-slim

# Install system dependencies for Tkinter and matplotlib
RUN apt-get update && apt-get install -y \
    python3-tk \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxft2 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Set display environment variable (for X11 forwarding)
ENV DISPLAY=:0

# Run the application
CMD ["python", "main.py"]
