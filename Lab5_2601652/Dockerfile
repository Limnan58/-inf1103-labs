FROM python:3.12-slim

WORKDIR /app

# Copy the script into the image
COPY inventory_manager.py .

# Create the mount point for the volume
RUN mkdir -p /app/data

# Run the program interactively
CMD ["python", "inventory_manager.py"]