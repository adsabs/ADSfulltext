
from __future__ import absolute_import, unicode_literals
from adsft import app as app_module
import adsputils
from adsft import exceptions
from adsft.models import KeyValue
from celery import Task
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue, BrokerConnection
import datetime


# ============================= INITIALIZATION ==================================== #

app = app_module.create_app()
exch = Exchange(app.conf.get('CELERY_DEFAULT_EXCHANGE', 'adsft'), 
                type=app.conf.get('CELERY_DEFAULT_EXCHANGE_TYPE', 'topic'))
app.conf.CELERY_QUEUES = (
    Queue('errors', exch, routing_key='errors', durable=False, message_ttl=24*3600*5),
    Queue('some-queue', exch, routing_key='check-orcidid')
)


logger = adsputils.setup_logging('adsft', app.conf.get('LOGGING_LEVEL', 'INFO'))


# connection to the other virtual host (for sending data out)
forwarding_connection = BrokerConnection(app.conf.get('OUTPUT_CELERY_BROKER',
                              '%s/%s' % (app.conf.get('CELRY_BROKER', 'pyamqp://'),
                                         app.conf.get('OUTPUT_EXCHANGE', 'other-pipeline'))))
class MyTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))



# ============================= TASKS ============================================= #

@app.task(base=MyTask, queue='some-queue')
def task_hello_world(message):
    """
    Fetch a message from the queue. Save it into the database.
    And print out into a log.
    

    :param: message: contains the message inside the packet
        {
         'name': '.....',
         'start': 'ISO8801 formatted date (optional), indicates 
             the moment we checked the orcid-service'
        }
    :return: no return
    """
    
    if 'name' not in message:
        raise exceptions.IgnorableException('Received garbage: {}'.format(message))
    
    with app.session_scope() as session:
        kv = session.query(KeyValue).filter_by(key=message['name']).first()
        if kv is None:
            kv = KeyValue(key=message['name'])
        
        now = adsputils.get_date()
        kv.value = now
        session.add(kv)
        session.commit()
        
        logger.info('Hello {key} we have recorded seeing you at {value}'.format(**kv.toJSON()))
        
        
    
    

if __name__ == '__main__':
    app.start()