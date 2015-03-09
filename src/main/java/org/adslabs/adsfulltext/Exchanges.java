//
// * @author     Jonny Elliott
// * @year       2015
// * @copyright  GNU General Public License v2
// * @credits
// * @version    0.1
// * @status     Development
//
// Class for the YAMLBeans ConfigLoader. Tells the layout of the Exchanges in the settings.yml file.
//
package org.adslabs.adsfulltext;

import java.util.Map;

public class Exchanges {

    public String exchange;
    public String exchange_type;
    public boolean durable;
    public boolean passive;
    public boolean autoDelete;
}