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

import org.junit.Test; // for @Test annotation
import org.junit.Ignore; // for @Ignore annotation
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*; // for assertThat()
import static org.hamcrest.CoreMatchers.containsString;
import org.json.JSONObject;
import org.json.JSONArray;
import java.util.List;
import java.util.concurrent.TimeUnit;

import org.adslabs.adsfulltext.PDFExtract;

public class PDFExtractTest {

    PDFExtract extractor = new PDFExtract();

    @Test
    public void testWorkerCanExtract() throws Exception {
        // Input file:
        //
        String test_pdf = getClass().getResource("/test_doc.pdf").getFile();
        String message = extractor.extract(test_pdf);
        assertThat(message, containsString("This is a PDF document"));
    }
}
