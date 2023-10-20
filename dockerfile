FROM python:3.10
RUN mkdir /usr/src/app agent
COPY .  /usr/src/app/onlineJudge
RUN pip install -r ./requirement.txt

CMD ["python" , "-u" , "server.py" ]