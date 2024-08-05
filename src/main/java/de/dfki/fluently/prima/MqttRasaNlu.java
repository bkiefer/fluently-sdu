package de.dfki.fluently.prima;

import java.io.File;
import java.util.Map;

import org.json.JSONObject;

import de.dfki.mlt.rudimant.agent.nlp.DialogueAct;
import de.dfki.mlt.rudimant.agent.nlp.RasaNlu;

public class MqttRasaNlu extends RasaNlu {
  private static final double DEFAULT_THRESHOLD = 0.75;

  // default is DEFAULT_THRESHOLD for both
  private double intent_confidence_threshold;
  private double entity_confidence_threshold;

  @Override
  public DialogueAct analyse(String text) {
    // TODO Auto-generated method stub
    return null;
  }

  @SuppressWarnings("rawtypes")
  @Override
  public boolean init(File configDir, String language, Map config) {
    try {
      Double d = (Double) config.get(CFG_MININTENT_CONFINDENCE);
      intent_confidence_threshold = d == null ? DEFAULT_THRESHOLD : d;
      d = (Double) config.get(CFG_MINENTITY_CONFINDENCE);
      entity_confidence_threshold = d == null ? DEFAULT_THRESHOLD : d;
    } catch (Exception ex) {
      logger.error(ex.getMessage());
      //return false;
      throw new RuntimeException(ex);
    }
    return super.init(configDir, language, config);
  }

  public DialogueAct convertNlu(JSONObject obj) {
    obj.put("minEntityConfidence", entity_confidence_threshold);
    DialogueAct r = convert(obj);
    if (r != null && r.hasSlot(CONFIDENCE_DAG_SLOT) &&
        Double.parseDouble(r.getValue(CONFIDENCE_DAG_SLOT)) < intent_confidence_threshold) {
      r = null;
    }
    if (r == null) {
      logger.info("No rasa NLU result");
    } else {
      logger.info("rasa: {}", r);
    }
    return r;
  }
}
