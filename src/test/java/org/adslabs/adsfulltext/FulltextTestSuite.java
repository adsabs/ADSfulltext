import org.junit.runner.RunWith;
import org.junit.runners.Suite;

// When a class is annotated with @RunWith, JUnit will invoke the class in which is annotated so as to run the tests, instead of using the runner built into JUnit.
@RunWith(Suite.class)

// The SuiteClasses annotation specifies the classes to be executed when a class annotated with @RunWith(Suite.class) is run.
@Suite.SuiteClasses({
   ConfigLoaderTest.class,
})

public class FulltextTestSuite {
}
