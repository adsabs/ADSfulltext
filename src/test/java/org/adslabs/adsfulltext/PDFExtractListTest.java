//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class is to test the PDFExtract class. This is purely a Unit test, and should not require any
// interaction with that of the RabbitMQ instance
//

import org.junit.Test;
import static org.hamcrest.CoreMatchers.containsString;
import static org.junit.Assert.*;
import org.json.JSONObject;
import org.json.JSONArray;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.adslabs.adsfulltext.PDFExtractList;

public class PDFExtractListTest {

    PDFExtractList extractor = new PDFExtractList();

    @Test
    public void testCanExtractJSONContentFromList() {
        String test_JSON = "[{\"test\": \"test\" }, {\"test2\": \"test2\"}]";

        List<JSONObject> result = extractor.convertJSONArrayToList(test_JSON);

        assertEquals(result.get(0).get("test"), "test");
        assertEquals(result.get(1).get("test2"), "test2");
    }

    @Test
    public void testWorkerCanExtractFromAnEntireList() {
        String testMessageJSON = "[{\"bibcode\": \"test\", \"file_format\": \"pdf\", \"UPDATE\": \"NOT_EXTRACTED_BEFORE\", \"meta_path\": \"some_path.json\", \"index_date\": \"2015-03-02T19:12:57.387093Z\", \"provider\": \"Elsevier\", \"ft_source\": \"/vagrant/src/test/resources/test_doc.pdf\"}, {\"bibcode\": \"test\", \"file_format\": \"pdf\", \"UPDATE\": \"NOT_EXTRACTED_BEFORE\", \"meta_path\": \"some_path.json\", \"index_date\": \"2015-03-02T19:12:57.387093Z\", \"provider\": \"Elsevier\", \"ft_source\": \"/vagrant/src/test/resources/test_doc.pdf\"}]";

        String result =  extractor.f(testMessageJSON);

        Pattern pattern = Pattern.compile("This is a PDF document");
        Matcher matcher = pattern.matcher(result);
        int count = 0;
        while (matcher.find()){
            count++;
        }

        assertThat(result, containsString("This is a PDF document"));

        // Check the number of times we have a string, so that we know it worked
        // on two sources
        assertEquals(2, count);

    }

}
