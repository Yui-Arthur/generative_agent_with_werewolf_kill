FROM python:3.10
RUN mkdir /usr/src/app agent
WORKDIR /usr/src/app/agent
COPY ./requirement.txt  .
RUN pip install -r ./requirement.txt
COPY . .

CMD ["sh" , "-c" , "python -u server.py --api_server ${api_server_ip} --docker"]