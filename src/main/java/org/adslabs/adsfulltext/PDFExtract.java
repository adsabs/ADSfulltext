//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class contains the functions to parse/extract the PDF file content, and whatever else is
// required. It is kept inside this extra class to make the code easier to read.
//
// Currently this skeleton contains the PDFBox extractor that does the following:
//
// 1. Load a Java InputStream object, pointing to the path of the file
// 2. Load a PDFBox Parser object that points to this file
// 3. Load and parse this PDF file with the PDFBox Parser
// 4. Extract the text from the virtual PDF file using PDFBox Stripper
//

package org.adslabs.adsfulltext;

import java.io.FileInputStream;

import org.apache.pdfbox.util.PDFTextStripper;
import org.apache.pdfbox.util.TextNormalize;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.cos.COSDocument;
import org.apache.pdfbox.pdfparser.PDFParser;


import org.json.JSONObject;
import org.json.JSONArray;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.text.Normalizer;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

public class PDFExtract {

    // Variable declaration
    // ------------------------
    String message;
    FileInputStream pdfFile;
    PDFTextStripper stripper;
    PDDocument pdDocument;
    PDFParser pdfParser;
    static Logger logger = LoggerFactory.getLogger(PDFExtract.class);
    // ------------------------

    // Constructor
    //
    public PDFExtract () {
        try {
            this.stripper = new PDFTextStripper();
        } catch (java.io.IOException error) {
            System.err.println("There is an error loading the PDFBox Stripper properties: " + error.getMessage());
        }
    }

    // ignore blobs of non-white characters longer than this length
    static int maxWordLength = 200;

    static String regexString = "\\S{" + (maxWordLength + 1) + ",}";
    static Pattern regexPattern = Pattern.compile(regexString);

    private static String trimWords (String buff) {
	// removes words which are longer than maxWordLength characters
	Matcher match = regexPattern.matcher(buff);
	if (match.find()) {
	    logger.debug("removing long text blobs from input buffer");
	    return buff.replaceAll(regexString, "");
	} else {
	    return buff;
	}
    }


    public String textCleaner (String messageToClean) {
        // Normalis(z)e the text so that we have the correct characters.
        // For example, an o-umlaut goes from o" to the correct formatting, this is normalising
        // For consistent comparison, I use the same naming convention as used by Jay
        TextNormalize normalizer = new TextNormalize("UTF-8");
        messageToClean = normalizer.normalizeDiac(messageToClean);
        messageToClean = normalizer.normalizePres(messageToClean);

        // This unifies characters such as e+accent to accented-e
        messageToClean = Normalizer.normalize(messageToClean, Normalizer.Form.NFKC);

        return trimWords(messageToClean);
    }

    // Main function that takes care of all the extraction regardless of the underlying process
    //
    public String extract (String fileSource) throws Exception {


        // Create the path to the PDF
        //
        try{
            logger.debug("Creating pdf file");
            this.pdfFile = new FileInputStream(fileSource);
        } catch (java.io.FileNotFoundException error) {
            String message = "File not found: " + error.getMessage();
            logger.error(message);
            throw new Exception(message, error);
        }

        // Create the PDF parser of the document of interest
        try {
            logger.debug("Creating PDF parser for the PDF file");
            this.pdfParser = new PDFParser(pdfFile);
        } catch (java.io.IOException error) {
            String message = "There is an error loading the COSDocument: " + error.getMessage();
            logger.error(message);
            throw new Exception(message, error);
        }

        // Parse the document and obtain the PDDocument, followed by extracting the content
        // Make sure we close the PDDocument at the end
        try {
            logger.debug("Parsing and extracting the PDF file");
            this.pdfParser.parse();
            this.pdDocument = this.pdfParser.getPDDocument();
            this.message = this.stripper.getText(pdDocument);

        } catch (java.io.IOException error) {
            String message = "There is an error parsing or loading the PDDocument or PDFBox Stripper: " + error.getMessage();
            logger.error(message);
            throw new Exception(message, error);
        } finally {
            try {
                logger.debug("Closing all relevant PDF content.");
                this.pdDocument.close();
            } catch (java.io.IOException error) {
                String message = "There is an error loading the PDFBox Stripper properties: " + error.getMessage();
                logger.error(message);
                throw new Exception(message, error);
            }

        }

        // Clean text
        this.message = this.textCleaner(this.message);

        return this.message;
    }
}
