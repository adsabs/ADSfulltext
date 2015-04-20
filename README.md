[![Build Status](https://travis-ci.org/adsabs/ADSfulltext.svg)](https://travis-ci.org/adsabs/ADSfulltext)
[![Coverage Status](https://coveralls.io/repos/adsabs/ADSfulltext/badge.svg)](https://coveralls.io/r/adsabs/ADSfulltext)
# ADSfulltext

Article full text exctraction pipeline based on advanced messaging queing protocol.

dev setup - vagrant (virtualbox)
================================

This is the easiest option. It will create a virtual machine using vagrant, start the required services (e.g., RabbitMQ) via docker. The adsfulltext directory is synced to /vagrant/ on the guest.

1. `vagrant up`
1. `vagrant ssh`
1. `cd /vagrant`

RabbitMQ
========

Access the GUI: http://localhost:15672

It is possible that the RabbitMQ instance will exit if your VM goes down. You can check and restart in the following way:

`docker ps -a`


>CONTAINER ID        IMAGE                        COMMAND             CREATED             STATUS                      PORTS                                              NAMES

>f03aef886092        dockerfile/rabbitmq:latest   "rabbitmq-start"    6 days ago          Exited (0) 55 seconds ago   0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp   dockerfile-rabbitmq   


`docker start f03aef886092`
>f03aef886092

`docker ps -a`
>CONTAINER ID        IMAGE                        COMMAND             CREATED             STATUS              PORTS                                              NAMES

>f03aef886092        dockerfile/rabbitmq:latest   "rabbitmq-start"    6 days ago          Up 49 seconds       0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp   dockerfile-rabbitmq
