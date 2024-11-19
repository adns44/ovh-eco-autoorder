FROM python:3-alpine

WORKDIR /app

ADD ./order.py ./order.py

CMD [ "python3", "/app/order.py" ]
