# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files to the work directory
COPY . /app/

# Copy the initialization script
COPY init.sh /app/

# Make the script executable
RUN chmod +x /app/init.sh

# Expose port 8000
EXPOSE 8000

# Set the entrypoint to the initialization script
ENTRYPOINT ["/app/init.sh"]
