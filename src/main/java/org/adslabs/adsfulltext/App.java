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

import org.adslabs.adsfulltext.Worker;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.Namespace;
import net.sourceforge.argparse4j.inf.MutuallyExclusiveGroup;
import net.sourceforge.argparse4j.impl.Arguments;

public class App {

    // Variable declaration
    // --------------------------
    static Logger logger = LoggerFactory.getLogger(App.class);
    // --------------------------

    public static void main(String[] args) {

        // Parsing details
        // -------------------------------------------------------------------

        ArgumentParser parser = ArgumentParsers.newArgumentParser("ADSfulltextPDF")
                .defaultHelp(true)
                .description("Application that starts workers for ADSfulltext PDF parsing.");

        boolean testRun = false;

        MutuallyExclusiveGroup flags = parser.addMutuallyExclusiveGroup("flags")
                .required(true);

        flags.addArgument("--no-consume-queue")
                .action(Arguments.storeTrue())
                .setDefault(testRun)
                .type(boolean.class)
                .help("Worker will exit the queue after consuming a single message.");

        flags.addArgument("--consume-queue")
                .action(Arguments.storeFalse())
                .setDefault(testRun)
                .help("Worker will sit on the queue, continuously consuming.");
        // -------------------------------------------------------------------
        Namespace ns = null;
        try {
            ns = parser.parseArgs(args);
        } catch (net.sourceforge.argparse4j.inf.ArgumentParserException error) {
            parser.handleError(error);
            System.exit(1);
        }

        testRun = ns.getBoolean("no_consume_queue") || ns.getBoolean("consume_queue");

        if (testRun) {
            logger.info("TestRun designated, will only consume once.");
        } else {
            logger.info("Normal consume designated, will consume until cancelled.");
        }

        // Initalise the worker
        logger.info("Instantiating the worker");
        Worker pdfWorker = new Worker(testRun);

        // Run the worker
        // This will:
        //  1. connect
        //  2. subscribe (start consuming)
        logger.info("Running the worker");
        pdfWorker.run();
        logger.info("Worker exited.");

        System.exit(0);
    }
}
