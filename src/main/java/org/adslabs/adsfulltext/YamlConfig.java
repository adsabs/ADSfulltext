//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// Class for the YAMLBeans ConfigLoader. Tells the layout of the entire settings.yml file.
//
package org.adslabs.adsfulltext;

import org.adslabs.adsfulltext.ErrorQueue;
import org.adslabs.adsfulltext.Exchanges;
import org.adslabs.adsfulltext.Queues;

import java.util.List;

public class YamlConfig {

    public String RABBITMQ_URI;
    public ErrorQueue ERROR_HANDLER;
    public Exchanges[] EXCHANGES;
    public Queues[] QUEUES;
}