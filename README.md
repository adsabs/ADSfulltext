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