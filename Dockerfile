FROM python:3-alpine

WORKDIR /app

ADD ./order.py ./order.py
ADD ./fetcher.py ./fetcher.py
ADD ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

CMD [ "python3", "/app/order.py" ]
