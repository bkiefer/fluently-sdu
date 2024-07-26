package de.dfki.vondabase;

import static de.dfki.vondabase.Constants.*;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Random;

import de.dfki.lt.hfc.WrongFormatException;
import de.dfki.lt.hfc.db.HfcDbHandler;
import de.dfki.lt.hfc.db.rdfProxy.Rdf;
import de.dfki.lt.hfc.db.rdfProxy.RdfProxy;
import de.dfki.mlt.rudimant.agent.Agent;
import de.dfki.mlt.rudimant.agent.Behaviour;
import de.dfki.mlt.rudimant.agent.nlp.DialogueAct;
import de.dfki.mlt.rudimant.agent.nlp.Pair;
import de.dfki.vondabase.utils.ExtendedBehaviour;

public abstract class BaseAgent extends Agent {
  /**
   * Some RDF Objects representing robots and user. Need to be adapted according
   * to project
   */
  public Rdf robot;
  public Rdf user;

  private HfcDbHandler handler = null;

  private RdfProxy startClient(File configDir, Map<String, Object> configs)
          throws IOException, WrongFormatException {
    String ontoFileName = (String) configs.get(CFG_ONTOLOGY_FILE);
    if (ontoFileName == null) {
      throw new IOException("Ontology file is missing.");
    }
    handler = new HfcDbHandler(ontoFileName);
    //handler = h;
    RdfProxy proxy = new RdfProxy(handler);
    handler.registerStreamingClient(proxy);
    return proxy;
  }

  @SuppressWarnings({"rawtypes", "unchecked"})
  public void init(File configDir, Map configs, String language)
          throws IOException, WrongFormatException {
    RdfProxy proxy = startClient(configDir, configs);
    init(configDir, language, proxy, configs, "dom:");
    //this.verbose = (boolean) configs.get(IS_VERBOSE);
    //TODO This is again project specific; needs to be adapted
    robot = _proxy.getRdf(ROBOT_URI);
    if (robot == null) {
      //System.err.println(_proxy.getClass(ROBOT_CLASS));
      robot = _proxy.getClass(ROBOT_CLASS).newRdf(ROBOT_URI);
    }
    user = _proxy.getRdf(USER_URI);
    if (user == null) {
      //System.err.println(_proxy.getClass(USER_CLASS));
      user = _proxy.getClass(USER_CLASS).newRdf(USER_URI);
    }
    if (configs.containsKey("filterRules")) {
      ruleLogger.filterUnchangedRules = (Boolean)configs.get("filterRules");
    }
    logAllRules();
  }

  @Override
  public void shutdown() {
    handler.shutdown();
    //if (server != null) server.shutdown();
    super.shutdown();
  }

  @Override
  protected Behaviour createBehaviour(int delay, DialogueAct da) {
    return createExtendedBehaviour(delay, da);
  }

  private Behaviour createExtendedBehaviour(int delay, DialogueAct da) {
    Pair<String, String> toSay = langServices.generate(da.getDag());
    if (toSay == null) {
      return new ExtendedBehaviour(generateId(), "error", "error", 0, da);
    }
    return new ExtendedBehaviour(generateId(), toSay.second, toSay.first, delay, da);
  }

  /* ===== Support Functions =============================================== */

  /**
   * retrieve information from informationstate
   * @param user
   * @return
   */
  public List<Object> getAllSessions(Rdf user) {
    // TODO: have a special Rdf.getAll(prop) method??
    return _proxy.query(
        "select ?sess where {} <dom:hasSession> ?sess ?_", user.getURI());
  }

  public Rdf getUser(String id) {
    // query db for user with id and return, or return null
    List<Object> result =
        query("select ?u where ?u <rdf:type> <dom:User> ?_ & ?u <dom:id> \"{}\" ?_");

    return result.isEmpty() ? null : (Rdf)result.get(0);
  }

  public Rdf getRandomItem (String type_uri) {
    String query = String.format(
        "select ?a where ?a <rdf:type> %s ?_", type_uri);
    List<Object> items = _proxy.query(query);
    Random rand = new Random();
    return items.isEmpty() ? null : (Rdf)items.get(rand.nextInt(items.size()));
  }

}
