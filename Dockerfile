FROM python:3.9.7

RUN mkdir /scale-plugin
RUN mkdir ~/.kube

WORKDIR /scale-plugin
 
ADD . .

RUN cp authority/config_server ~/.kube/config

RUN pip install kubernetes

CMD ["python", "./main.py"]