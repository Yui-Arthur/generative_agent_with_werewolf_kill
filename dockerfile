FROM python:3.10
RUN mkdir /usr/src/app agent
WORKDIR /usr/src/app/agent
COPY .  .
RUN pip install -r ./requirement.txt

CMD ["sh" , "-c" , "python -u server.py --api_server ${api_server_ip}"]