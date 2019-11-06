LOGGING_LEVEL = 'DEBUG'

CELERY_BROKER = 'pyamqp://guest@localhost:6672/fulltext_pipeline'
PDF_EXTRACTOR = 'org.adslabs.adsfulltext.PDFExtractList'

#GROBID_SERVICE = 'http://localhost:8080/processFulltextDocument'
GROBID_SERVICE = None # Disable

EXTRACT_PDF_SCRIPT = '/scripts/extract_pdf_with_pdftotext.sh'
#EXTRACT_PDF_SCRIPT = '/scripts/extract_pdf_with_pdfbox.sh'

OUTPUT_CELERY_BROKER = 'pyamqp://guest:guest@localhost:6672/master_pipeline'
OUTPUT_TASKNAME = 'adsmp.tasks.task_update_record'

PREFERRED_XML_PARSER_NAMES = ("html5lib", "html.parser", "lxml-html", "direct-lxml-html", "lxml-xml", "direct-lxml-xml",)

FULLTEXT_EXTRACT_PATH = './live'


