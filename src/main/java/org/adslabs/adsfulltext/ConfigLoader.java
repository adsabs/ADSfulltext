package org.adslabs.adsfulltext;

import com.esotericsoftware.yamlbeans.YamlReader;

import javax.sound.midi.SysexMessage;
import java.io.FileReader;
import java.util.Map;


public class ConfigLoader {


    // Definitions of constants
    private String name;

    // Class Constructor
    public ConfigLoader () {
        this.setName("/settings.yml");
    }

    private void setName(String givenName) {
        this.name = givenName;
    }

    public String getName() {
        return this.name;
    }

    public void loadYAML () {

        try {
            String resource = getClass().getResource(this.getName()).getFile();
            FileReader newInputFile = new FileReader(resource);

            YamlReader reader = new YamlReader(newInputFile);
            Object object = reader.read();
            System.out.println(object);
            Map map = (Map) object;

            this.setName(map.get("FULLTEXT_EXTRACT_PATH").toString());

        } catch (java.io.FileNotFoundException error) {
            System.out.println(error.getStackTrace());
            this.setName("failed");
        } catch (com.esotericsoftware.yamlbeans.YamlException error) {
            System.out.println(error.getStackTrace());
        }
    }

}
