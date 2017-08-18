LOGGING_LEVEL = 'DEBUG'

CELERY_BROKER = 'pyamqp://guest@localhost:6672/fulltext_pipeline'
PDF_EXTRACTOR = 'org.adslabs.adsfulltext.PDFExtractList'

GROBID_SERVICE = 'http://localhost:8080/processFulltextDocument'

OUTPUT_CELERY_BROKER = 'pyamqp://guest:guest@localhost:6672/master_pipeline'
OUTPUT_TASKNAME = 'adsmp.tasks.task_update_record'


FULLTEXT_EXTRACT_PATH = './live'


