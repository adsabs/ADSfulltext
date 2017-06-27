from .models import KeyValue
import adsputils
from celery import Celery
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker




def create_app(app_name='adsft',
               local_config=None):
    """Builds and initializes the Celery application."""
    
    conf = adsputils.load_config()
    if local_config:
        conf.update(local_config)

    app = adsftCelery(app_name,
             broker=conf.get('CELERY_BROKER', 'pyamqp://'),
             include=conf.get('CELERY_INCLUDE', ['adsft.tasks']))

    app.init_app(conf)
    return app



class adsftCelery(Celery):
    
    def __init__(self, app_name, *args, **kwargs):
        Celery.__init__(self, *args, **kwargs)
        self._config = adsputils.load_config()
        self._session = None
        self._engine = None
        self._app_name = app_name
        self.logger = adsputils.setup_logging(app_name) #default logger
        
    

    def init_app(self, config=None):
        """This function must be called before you start working with the application
        (or worker, script etc)
        
        :return None
        """
        
        if self._session is not None: # the app was already instantiated
            return
        
        if config:
            self._config.update(config) #our config
            self.conf.update(config) #celery's config (devs should be careful to avoid clashes)
        
        self.logger = adsputils.setup_logging(self._app_name, self._config.get('LOGGING_LEVEL', 'INFO'))
        self._engine = create_engine(config.get('SQLALCHEMY_URL', 'sqlite:///'),
                               echo=config.get('SQLALCHEMY_ECHO', False))
        self._session_factory = sessionmaker()
        self._session = scoped_session(self._session_factory)
        self._session.configure(bind=self._engine)
    
    
    def close_app(self):
        """Closes the app"""
        self._session = self._engine = self._session_factory = None
        self.logger = None
    
        
    @contextmanager
    def session_scope(self):
        """Provides a transactional session - ie. the session for the 
        current thread/work of unit.
        
        Use as:
        
            with session_scope() as session:
                o = ModelObject(...)
                session.add(o)
        """
    
        if self._session is None:
            raise Exception('init_app() must be called before you can use the session')
        
        # create local session (optional step)
        s = self._session()
        
        try:
            yield s
            s.commit()
        except:
            s.rollback()
            raise
        finally:
            s.close()  
            
