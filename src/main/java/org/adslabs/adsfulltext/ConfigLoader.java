package org.adslabs.adsfulltext;

import com.esotericsoftware.yamlbeans.YamlReader;

import java.io.FileReader;
import java.util.Map;


public class ConfigLoader {

    // Definitions of constants
    private String configFileName;


    public void setConfigFileName (String configFileName) {this.configFileName = configFileName; }
    public String getConfigFileName () {return this.configFileName; }

    public YamlConfig data;

    // Class Constructor
    public ConfigLoader () {
        this.setConfigFileName("/settings.yml");
    }

    public void loadConfig () {

        try {
            String resource = getClass().getResource(this.getConfigFileName()).getFile();
            FileReader newInputFile = new FileReader(resource);

            YamlReader reader = new YamlReader(newInputFile);
            this.data = reader.read(YamlConfig.class);

        } catch (java.io.FileNotFoundException error) {
            System.out.println("FileNotFoundError: " + error.getStackTrace());

        } catch (com.esotericsoftware.yamlbeans.YamlException error) {
            System.out.println("YamlExceptionError: " + error.getStackTrace());

        }
    }
}