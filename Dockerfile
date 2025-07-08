# Use a Python base image
FROM python:3.13-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy pyproject.toml for dependency management
COPY pyproject.toml ./

# Install dependencies using pip
RUN pip install --no-cache-dir \
    "dotenv>=0.9.9" \
    "serpapi>=0.1.5" \
    "fastapi>=0.110.0" \
    "uvicorn>=0.22.0"

# Copy the rest of the application code
COPY . .

# Create the logs directory
RUN mkdir -p logs

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]