FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN python -c "
import os
for root, dirs, files in os.walk('/app'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            data = open(path, 'rb').read()
            nulls = data.count(b'\x00')
            if nulls > 0:
                print('NULL BYTES in ' + path + ': ' + str(nulls))
            else:
                print('OK: ' + path)
"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]