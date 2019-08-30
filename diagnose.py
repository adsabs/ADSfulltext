from adsft.extraction import StandardExtractorXML, StandardElsevierExtractorXML
import os

# read list of xml paths
#dir = './tests/test_integration/stub_data/full_test.xml'
#dir = './tests/test_integration/stub_data/full_test_elsevier.xml'
dir = './tests/test_unit/stub_data/test.xml'
#dir = '/proj/ads/fulltext/sources/EOSTr/0094/eost2013EO520007.wml2.xml'

m = {
    'ft_source': dir,
    'file_format': 'xml',
    'provider': 'MNRAS',
    'bibcode': 'test'
}

output = StandardExtractorXML(m).extract_multi_content()

print(output['fulltext'])
