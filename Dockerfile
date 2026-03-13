FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN python -c "import os; [print('NULL BYTES in ' + os.path.join(r,f) + ': ' + str(open(os.path.join(r,f),'rb').read().count(b'\x00'))) for r,d,files in os.walk('/app') for f in files if f.endswith('.py')]"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]