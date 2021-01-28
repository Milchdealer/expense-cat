FROM python:3.9-slim
LABEL MAINTAINER="Milchdealer/Teraku"

WORKDIR /usr/src/app

RUN pip install --no-cache-dir pip install matplotlib numpy

COPY src/main.py .

CMD ["python", "./main.py"]
