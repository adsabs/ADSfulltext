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

import java.util.concurrent.TimeUnit;

import org.adslabs.adsfulltext.PDFExtract;

public class PDFExtractTest {

    PDFExtract extractor = new PDFExtract();

    @Test
    public void testWorkerCanExtract() {
        // Input file:
        //
        String test_pdf = "/vagrant/src/test/resources/test_doc.pdf";
        String message = extractor.f(test_pdf);
        System.out.println("This is an obtained message: " + message);
        assertThat(message, containsString("This is a PDF document"));
    }

}
