FROM python:3.11-slim
RUN pip install paho-mqtt flask --quiet
WORKDIR /app
COPY subscriber.py web.py ./
CMD sh -c "python subscriber.py & python web.py"
