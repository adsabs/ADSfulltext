//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class is to test the PDFExtractList class. This is purely a Unit test, and should not require any
// interaction with that of the RabbitMQ instance
//

package org.adslabs.adsfulltext;

import java.util.ArrayList;
import java.util.List;
import org.json.JSONObject;
import org.json.JSONArray;

import org.adslabs.adsfulltext.PDFExtract;

public class PDFExtractList {

    public String f (String UnparsedRabbitMQPayload) throws Exception {

        // Variable declaration
        // ------------------------
        JSONArray ParsedRabbitMQPayload;
        // ------------------------

        // Parse the content of the input
        ParsedRabbitMQPayload = new JSONArray(UnparsedRabbitMQPayload);

        // For each of the articles in the payload
        for(int i=0; i<ParsedRabbitMQPayload.length(); i++){

            PDFExtract pdfFile = new PDFExtract();

            // Extract the full text
            JSONObject tempPayload = ParsedRabbitMQPayload.getJSONObject(i);
            String fileSource = (String) tempPayload.get("ft_source");
            String message = pdfFile.extract(fileSource);

            // Put the fulltext into the RabbitMQ payload
            tempPayload.put("fulltext", message);
        }

        return ParsedRabbitMQPayload.toString();
    }
}