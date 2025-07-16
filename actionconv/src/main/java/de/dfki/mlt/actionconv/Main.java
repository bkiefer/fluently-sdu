package de.dfki.mlt.actionconv;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Date;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.AddImport;
import org.semanticweb.owlapi.model.EntityType;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLAnnotationProperty;
import org.semanticweb.owlapi.model.OWLAxiom;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassAssertionAxiom;
import org.semanticweb.owlapi.model.OWLDataFactory;
import org.semanticweb.owlapi.model.OWLDataProperty;
import org.semanticweb.owlapi.model.OWLDataPropertyAssertionAxiom;
import org.semanticweb.owlapi.model.OWLImportsDeclaration;
import org.semanticweb.owlapi.model.OWLNamedIndividual;
import org.semanticweb.owlapi.model.OWLObjectProperty;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.model.OWLOntologyStorageException;
import org.semanticweb.owlapi.model.PrefixManager;
import org.semanticweb.owlapi.util.DefaultPrefixManager;
import org.semanticweb.owlapi.util.SimpleIRIMapper;
import org.yaml.snakeyaml.Yaml;

public class Main implements AutoCloseable {
  private class ParseException extends RuntimeException {
    private static final long serialVersionUID = -7082461845237896276L;

    public ParseException(String msg) {
      super(msg);
    }
  }

  private class OwlMapEntry {
    String xsdType;
    String key;

    OWLDataProperty odp;

    OwlMapEntry(String k, String t) {
      key = k;
      xsdType = t;
    }
  }


  public static final IRI planns = IRI
      .create("http://www.fluently.eu/2025/04/planner#", "");
  public static final String planner_file = "planner.owl";
  public static IRI ns = planns;
  public static String data_file = "";

  private final OWLOntologyManager man;
  private final OWLOntology onto;
  private final OWLDataFactory df;
  private final PrefixManager plan;

  private OWLClass owlBasicConditionClass;
  private OWLClass owlAskQueryCondtionClass;
  private OWLClass owlAllQueryCondtionClass;
  private OWLClass owlSomeQueryConditionClass;


  private OWLClass owlConjunctionClass;
  private OWLClass owlDisjunctionClass;
  private OWLClass owlNegationClass;

  private OWLClass owlActionClass;

  private OWLDataProperty basicCondition;
  private OWLDataProperty rdlQuery;
  private OWLDataProperty description;
  private OWLDataProperty name;

  private OWLObjectProperty condition;
  private OWLObjectProperty conditions;
  private OWLObjectProperty postCondition;

  @SuppressWarnings("serial")
  private final HashMap<String, OwlMapEntry> props = new HashMap<>() {
    {
      //put("basicCondition", new OwlMapEntry("basicCondition", "xsd:string"));
      //put("rdlQuery", new OwlMapEntry("rdlQuery", "xsd:string"));
      //put("description", new OwlMapEntry("description", "xsd:string"));
    }
  };

  public Main(File ontoFile)
      throws OWLOntologyCreationException {
    man = OWLManager.createOWLOntologyManager();
    onto = man.createOntology(ns); // create empty ontology
    df = onto.getOWLOntologyManager().getOWLDataFactory();
    plan = new DefaultPrefixManager(ns.getNamespace());

    SimpleIRIMapper iriMapper = new SimpleIRIMapper(planns,
        IRI.create(ontoFile));
    man.getIRIMappers().add(iriMapper);

    // add import of base ontology to this ontology
    OWLImportsDeclaration importDecl = df.getOWLImportsDeclaration(
        IRI.create(planns.getNamespace().replace("#", "")));
    man.applyChange(new AddImport(onto, importDecl));
    plan.setPrefix("plan:", planns.getNamespace());

    for (Map.Entry<String, OwlMapEntry> entry : props.entrySet()) {
      OwlMapEntry e = entry.getValue();
      e.odp = df.getOWLDataProperty("plan:" + e.key, plan);
    }
    owlBasicConditionClass = df.getOWLClass("plan:BasicCondition", plan);
    owlAskQueryCondtionClass = df.getOWLClass("plan:AskQueryCondition", plan);
    owlAllQueryCondtionClass = df.getOWLClass("plan:AllQueryCondition", plan);
    owlSomeQueryConditionClass = df.getOWLClass("plan:SomeQueryCondition", plan);
    owlConjunctionClass = df.getOWLClass("plan:Conjunction", plan);
    owlDisjunctionClass = df.getOWLClass("plan:Disjunction", plan);
    owlNegationClass = df.getOWLClass("plan:Negation", plan);

    basicCondition = df.getOWLDataProperty("plan:basicCondition", plan);
    rdlQuery = df.getOWLDataProperty("plan:rdlQuery", plan);
    description = df.getOWLDataProperty("plan:description", plan);
    name = df.getOWLDataProperty("plan:name", plan);

    owlActionClass = df.getOWLClass("plan:Action", plan);
    condition = df.getOWLObjectProperty("plan:condition", plan);
    conditions = df.getOWLObjectProperty("plan:conditions", plan);
    postCondition = df.getOWLObjectProperty("plan:postCondition", plan);
  }

  private void addPropertyValue(OWLNamedIndividual individual,
      OWLDataProperty prop, double val) {
    OWLAxiom axiom = df.getOWLDataPropertyAssertionAxiom(prop, individual,
        df.getOWLLiteral(val));
    man.addAxiom(onto, axiom);
  }

  private void addPropertyValue(OWLNamedIndividual individual,
      OWLDataProperty prop, int val) {
    OWLAxiom axiom = df.getOWLDataPropertyAssertionAxiom(prop, individual,
        df.getOWLLiteral(val));
    man.addAxiom(onto, axiom);
  }

  private void addPropertyValue(OWLNamedIndividual individual,
      OWLDataProperty prop, boolean val) {
    OWLAxiom axiom = df.getOWLDataPropertyAssertionAxiom(prop, individual,
        df.getOWLLiteral(val));
    man.addAxiom(onto, axiom);
  }

  private void addPropertyValue(OWLNamedIndividual individual,
      OWLDataProperty prop, String val) {
    OWLAxiom axiom = df.getOWLDataPropertyAssertionAxiom(prop, individual,
        df.getOWLLiteral(val));
    man.addAxiom(onto, axiom);
  }

  private void addPropertyValue(OWLNamedIndividual individual,
      OWLObjectProperty prop, String iri, PrefixManager mngr) {
    OWLAxiom axiom = df.getOWLObjectPropertyAssertionAxiom(prop, individual,
        df.getOWLNamedIndividual(iri, mngr));
    man.addAxiom(onto, axiom);
  }

  private void addPropertyValue(OWLNamedIndividual subject,
      OWLObjectProperty prop, OWLNamedIndividual object, PrefixManager mngr) {
    OWLAxiom axiom = df.getOWLObjectPropertyAssertionAxiom(prop, subject,
        object);
    man.addAxiom(onto, axiom);
  }

  public OWLNamedIndividual createIndividual(PrefixManager pm,
      OWLDataFactory fact, String id) {
    String suffix = ":" + id;
    OWLNamedIndividual indiv = fact.getOWLNamedIndividual(suffix, pm);
    return indiv;
  }

  int ID = (int) (Math.random() * (new Date().getTime() / 10000000000l));

  public String newId(String prefix) {
    return String.format("%s%0,5d", prefix, ++ID);
  }

  public OWLNamedIndividual createConj(OWLNamedIndividual arg0,
      OWLNamedIndividual arg1) {
    OWLNamedIndividual conj;
    if (arg0.getIRI().getIRIString().contains("#Conj")) {
      conj = arg0;
    } else {
      String id = newId("Conj");
      conj = createEntityWithClass(id, owlConjunctionClass);
      addPropertyValue(conj, conditions, arg0, plan);
    }
    addPropertyValue(conj, conditions, arg1, plan);
    return conj;
  }

  public OWLNamedIndividual createDisj(OWLNamedIndividual arg0,
      OWLNamedIndividual arg1) {
    OWLNamedIndividual disj;
    if (arg0.getIRI().getIRIString().contains("#Disj")) {
      disj = arg0;
    } else {
      String id = newId("Disj");
      disj = createEntityWithClass(id, owlDisjunctionClass);
      addPropertyValue(disj, conditions, arg0, plan);
    }
    addPropertyValue(disj, conditions, arg1, plan);
    return disj;
  }

  public OWLNamedIndividual createNeg(OWLNamedIndividual arg0) {
    String id = newId("Neg");
    OWLNamedIndividual conj = createEntityWithClass(id, owlNegationClass);
    addPropertyValue(conj, condition, arg0, plan);
    return conj;
  }

  Map<String, OWLNamedIndividual> atomics = new HashMap<>();

  public OWLNamedIndividual createBasic(String id) {
    // get it from internal map
    if (! atomics.containsKey(id)) {
      throw new ParseException(id + " is not a valid atomic condition");
    }
    return atomics.get(id);
  }

  public OWLNamedIndividual createEntityWithClass(String name, OWLClass clazz) {

    // Create entity
    OWLNamedIndividual owlEntity = createIndividual(plan, df, name);

    // Set type of new entity
    OWLClassAssertionAxiom assertion = df.getOWLClassAssertionAxiom(clazz,
        owlEntity);
    man.addAxiom(onto, assertion);

    return owlEntity;
  }

  /** Create an atomic condition
   *
   * @param atomic a triple: name, code, description
   */
  public void processAtomic(List<String> atomic) {
    OWLNamedIndividual cond = null;
    String id = atomic.get(0);
    if (atomic.get(1).toLowerCase().startsWith("select")) {
      if (atomic.size() == 3) {
        // ask query
        cond = createEntityWithClass(id, owlAskQueryCondtionClass);
        addPropertyValue(cond, rdlQuery, atomic.get(1));
        addPropertyValue(cond, description, atomic.get(2));
      } else {
        if (atomic.get(3).charAt(0) == 'A') {
          // all query
        } else {
          // some query
        }
      }
    } else {
      cond = createEntityWithClass(id, owlBasicConditionClass);
      addPropertyValue(cond, basicCondition, atomic.get(1));
      addPropertyValue(cond, description, atomic.get(2));
    }
    atomics.put(id, cond);
  }

  OWLNamedIndividual parseCondition(String expression) {
    if (expression == null || expression.isBlank()) return null;
    CondParser p = new CondParser(new Lexer(new StringReader(expression)));
    p.main = this;
    try {
      if (p.parse()) return p._cond;
    } catch (IOException ex) {
      // never happens, String IO
    } catch (ParseException pex) {
      System.out.println(pex);
    }
    return null;
  }

  public void addCondition(OWLNamedIndividual act, Map<String, String> conds,
      String id, String what, OWLObjectProperty prop) {
    if (conds.containsKey(what)) {
      OWLNamedIndividual cond = parseCondition(conds.get(what));
      if (cond == null) {
        System.out.println("Wrong or illegal condition for "
            + what + " of  action " + id);
        System.exit(1);
      }
      addPropertyValue(act, prop, cond, plan);
    }
  }

  public void processAction(Map<String, Object> action) {
    assert action.keySet().size() == 1;
    String id = action.keySet().iterator().next();
    @SuppressWarnings("unchecked")
    Map<String, String> conds = (Map<String, String>) action.get(id);
    OWLNamedIndividual act = createEntityWithClass(id, owlActionClass);
    addPropertyValue(act, name, id);
    addCondition(act, conds, id, "pre", condition);
    addCondition(act, conds, id, "post", postCondition);
  }


  private boolean isTrue(String val) {
    String[] yes = { "true", "yes" };
    return Arrays.binarySearch(yes, val.toLowerCase()) >= 0;
  }


  public void saveOntology(File where)
      throws OWLOntologyStorageException, FileNotFoundException {
    man.saveOntology(onto, new FileOutputStream(where));
  }

  @SuppressWarnings("unchecked")
  public static void main(String[] args) throws IOException {

    /* *********************************************************************
     * Checking input
     * ********************************************************************/
    System.out.println("### Checking input...");
    if (args.length < 2) {
      System.out.println(
          "Usage: run.sh <base_ontology.owl> <actiondefs.yml> [ontoname (default actions)]\n"
              + "Aborting...");
      return;
    }
    System.out.printf("Provided base ontology file: %s %n", args[0]);
    System.out.printf("Provided action definitions file: %s %n", args[1]);
    File inputFile = new File(args[1]);
    File ontologyFile = new File(args[0]);

    String ontoname = "actions";
    if (args.length > 2) {
      ontoname = args[2];
    }
    ns = IRI.create("http://www.dfki.de/mlt/fluently/" + ontoname + "#");
    data_file = ontoname + ".owl";

    Path out = ontologyFile.toPath();
    Path outputFile = out.getParent();
    outputFile = outputFile.resolve(data_file);
    Files.createDirectories(outputFile.getParent());
    System.out.printf("New .owl file will be named %s %n", outputFile);

    /* *********************************************************************
     * Loading base ontology
     * ********************************************************************/
    System.out.print("### Loading base ontology ... ");
    try (Main main = new Main(ontologyFile)) {
      System.out.println("loaded.");

      /* *********************************************************************
       * Parsing .yaml file and adding entries to ontology
       * ********************************************************************/
      System.out.print("### Reading actions file ...");

      Yaml yaml = new Yaml();
      Map<String,Object> defs = yaml.load(new FileReader(inputFile));
      System.out.print(" basic conditions ...");
      for (List<String> atomic : (List<List<String>>)defs.get("atomic")) {
        main.processAtomic(atomic);
      }
      System.out.print(" actions ...");
      for (Map<String, Object> action : (List<Map<String, Object>>)defs.get("actions")) {
        main.processAction(action);
      }
      System.out.println(" read.");

      /* *********************************************************************
       * Save ontology
       * ********************************************************************/
      System.out.print("### Saving .owl file ... ");
      main.saveOntology(outputFile.toFile());
      System.out.println("saved.");
    } catch (Exception e) {
      e.printStackTrace();
    }
  }


  @Override
  public void close() throws Exception {
    // TODO Auto-generated method stub

  }

}
