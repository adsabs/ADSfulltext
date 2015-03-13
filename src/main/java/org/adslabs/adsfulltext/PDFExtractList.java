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


    public List<JSONObject> convertJSONArrayToList (String RabbitMQPayload) {

        // This converts the incoming string from RabbitMQ into a usable
        // Java ArrayList that contains JSONObjects. JSONObjects are similar
        // to the lists

        JSONArray jsonPayload = new JSONArray(RabbitMQPayload);
        List<JSONObject> payloadList = new ArrayList<JSONObject>();

        for(int i=0; i<jsonPayload.length(); i++){
            payloadList.add(jsonPayload.getJSONObject(i));
        }

        return payloadList;
    }

    public String f (String UnparsedRabbitMQPayload){

        // Variable declaration
        // ------------------------
        List<JSONObject> ParsedRabbitMQPayload;
        String JSONFullTextPayload;
        // ------------------------

        // Parse the content of the input
        ParsedRabbitMQPayload = this.convertJSONArrayToList(UnparsedRabbitMQPayload);

        // For each of the articles in the payload
        for(int i=0; i<ParsedRabbitMQPayload.size(); i++){

            PDFExtract pdfFile = new PDFExtract();

            // Extract the full text
//            System.out.println(ParsedRabbitMQPayload.get(i).get("ft_source").getClass().getName());
            JSONObject tempPayload = ParsedRabbitMQPayload.get(i);
            String fileSource = (String) tempPayload.get("ft_source");
            String message = pdfFile.extract(fileSource);

            // Put the fulltext into the RabbitMQ payload
            tempPayload.put("fulltext", message);
        }

        // Convert back to JSON
        JSONFullTextPayload = ParsedRabbitMQPayload.toString();

        return JSONFullTextPayload;
    }

}
