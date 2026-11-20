FROM python:3.12-slim

WORKDIR /app

# Copy all the Python modules (main program + classes) into the image
COPY *.py ./

# Create the mount point for the volume
RUN mkdir -p /app/data

# Run the program interactively
CMD ["python", "inventory_manager.py"]
