
CELERY_BROKER = 'pyamqp://guest@localhost:6672/fulltext_pipeline'
PDF_EXTRACTOR = 'org.adslabs.adsfulltext.PDFExtractList'


OUTPUT_CELERY_BROKER = 'pyamqp://guest:guest@localhost:6672/master_pipeline'
OUTPUT_TASKNAME = 'adsmp.tasks.task_update_record'


FULLTEXT_EXTRACT_PATH = './live'


