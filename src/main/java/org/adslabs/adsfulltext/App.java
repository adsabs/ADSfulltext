//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// This class is the main application layer that starts the Java PDF Extractor. This should be activated by,
// and maintained by supervisord.
//

package org.adslabs.adsfulltext;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;
import net.sourceforge.argparse4j.inf.MutuallyExclusiveGroup;
import net.sourceforge.argparse4j.impl.Arguments;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.lang.String;
import java.io.IOException;

public class App {

    // Variable declaration
    // --------------------------
    static Logger logger = LoggerFactory.getLogger(App.class);
    // --------------------------

    public static void main(String[] args) throws Exception {

        // Parsing details
        // -------------------------------------------------------------------

        ArgumentParser parser = ArgumentParsers.newArgumentParser("ExtractPDF")
                .defaultHelp(true)
                .description("Application for extracting fulltext from PDF.");
        parser.addArgument("pdfs")
              .metavar("N")
              .type(String.class)
              .nargs("+")
              .help("Location of the source pdf[| + output path to save results to]");
        // -------------------------------------------------------------------
        Namespace ns = null;
        try {
            ns = parser.parseArgs(args);
        } catch (net.sourceforge.argparse4j.inf.ArgumentParserException error) {
            parser.handleError(error);
            System.exit(1);
        }

         
        PDFExtract extractor = new PDFExtract();
        String result = null;
        
        for (String file: (List<String>) ns.get("pdfs")) {
          if (file.indexOf("|") > -1) {
            String[] parts = file.split("\\|");
            if (parts.length != 2) {
              logger.info("Ignoring erroneous input: " + file);
            }
            else {
              logger.debug("Extracting: " + parts[0]);
              try {
                result = extractor.extract(parts[0]);
                Files.write(Paths.get(parts[1]), result.getBytes(StandardCharsets.UTF_8));
              }
              catch (IOException e) {
                logger.error("Failed extracting {}, error: {}", file, e.getMessage());
                e.printStackTrace();
              }
            }
          }
          else {
            logger.debug("Extracting: " + file);
            System.out.print(extractor.extract(file));
          }
        }

        System.exit(0);
    }
}
