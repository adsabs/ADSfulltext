'''
Pipeline to extract full text documents. It carries out the following:


  - Initialises the queues to be used in RabbitMQ
'''

from workers import RabbitMQWorker

class Singleton:
	
	_instances = {}
	
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]

class TaskMaster(Singleton):
	def __init__(self, rabbitmq_url, rabbitmq_routes, workers):
		self.rabbitmq_url = rabbitmq_url
		self.rabbitmq_routes = rabbitmq_routes
		self.workers = workers

	def initialize_rabbitmq(self):
		#Make sure the plumbing in rabbitMQ is correct; this procedure is idempotent
		w = RabbitMQWorker()
		w.connect(self.rabbitmq_url)
		w.declare_all(*[self.rabbitmq_routes[i] for i in ['EXCHANGES','QUEUES','BINDINGS']])
		w.connection.close()

	# def getLock(self):
	# 	self.lockfile = Lockfile()
	# 	self.lockfile.acquire()

	# def quit(self,signal,frame):
	# 	#Kill child workers if master gets SIGTERM
	# 	try:
	# 		self.stop_workers()
	# 	except Exception, err:
	# 		logger.warning("Workers not stopped gracefully: %s" % err)
	# 	finally:
	# 		if not self.lockfile.release():
	# 		logger.warning("Lockfile [%s] wasn't removed properly" % (self.lockfile.path))
	# 		self.running = False
	# 		sys.exit(0)
