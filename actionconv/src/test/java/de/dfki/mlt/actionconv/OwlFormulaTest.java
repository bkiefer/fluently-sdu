package de.dfki.mlt.actionconv;

import static org.junit.Assert.*;

import java.io.File;
import java.io.FileReader;

import org.junit.Test;

public class OwlFormulaTest {

  public static String RESOURCE_DIR = "src/test/resources/" ;
  public static String PLANNERONTO =
      "../src/main/resources/ontology/fluently/planner.owl";


  @Test
  public void owlFormulaTest() throws Exception {
    Main m = new Main(new File(PLANNERONTO));
    m.readDefinitions(new FileReader(RESOURCE_DIR + "testactions.yml"));
    assertEquals(18, m.atomics.size());
    assertEquals(21, m.actions.size());
    m.close();
    // hmm, how to test if everything went right?
    // We'll wait for the next error to come up and put it here.
  }


}
