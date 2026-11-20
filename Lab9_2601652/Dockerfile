FROM python:3.12-slim

WORKDIR /app

# Copy the Python modules, the sample products file and the tests folder
COPY *.py products.csv ./
COPY tests/ ./tests/

# Create the mount point for the volume
RUN mkdir -p /app/data

# Run the program interactively (default)
# Run the tests instead with:
#   docker run --rm inventory-lab9 python -m unittest discover -s tests -t . -v
CMD ["python", "inventory_manager.py"]
