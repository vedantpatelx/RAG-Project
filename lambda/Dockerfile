FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum install -y gcc gcc-c++ make && yum clean all

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY ingestion_handler.py .

CMD ["ingestion_handler.handler"]