package de.dfki.fluently.prima;

import static de.dfki.fluently.prima.Constants.ASR_TOPIC;
import static de.dfki.fluently.prima.Constants.OUT_TOPIC;
import static de.dfki.fluently.prima.Constants.TTS_TOPIC;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.Set;

import org.eclipse.paho.client.mqttv3.MqttException;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import de.dfki.fluently.prima.data.AsrResult;
import de.dfki.fluently.prima.utils.Listener;
import de.dfki.lt.hfc.WrongFormatException;
import de.dfki.mlt.mqtt.JsonMarshaller;
import de.dfki.mlt.mqtt.MqttHandler;
import de.dfki.mlt.rudimant.agent.Behaviour;
import de.dfki.mlt.rudimant.agent.CommunicationHub;
import de.dfki.mlt.rudimant.agent.Intention;
import de.dfki.mlt.rudimant.agent.nlp.DialogueAct;


public class BaseCommunicationHub implements CommunicationHub {

  private final static Logger logger = LoggerFactory.getLogger(BaseCommunicationHub.class);

  /**
   * How much time in milliseconds must pass between two behaviours, if
   * no message came back that the previous behaviour was finished.
   */
  public static long MIN_TIME_BETWEEN_BEHAVIOURS = 10000;
  private final Deque<Object> inQueue = new ArrayDeque<>();
  private final Deque<Object> itemsToSend = new ArrayDeque<>();

  private final Deque<Object> pendingEvents = new ArrayDeque<>();
  // Define a set of EventListener -> these are used to trigger audio output, update the avatar and so on
  private final List<Listener<Behaviour>> _listeners = new ArrayList<>();

  private final Random r = new Random();
  private boolean isRunning = true;
  private BaseAgent _agent;

  private MqttHandler client;
  private JsonMarshaller mapper;

  private MqttRasaNlu mqttRasa;

  private boolean receiveAsr(byte[] b) {
    Optional<AsrResult> cmd;
    (cmd = mapper.unmarshal(b, AsrResult.class)).ifPresent(this::sendEvent);
    if (! cmd.isEmpty()) {
      sendEvent(cmd.get());
    }
    return ! cmd.isEmpty();
  }

  private boolean receiveNlu(byte[] b) {
    try {
      String jsonResult = new String(b, StandardCharsets.UTF_8);
      JSONObject obj = new JSONObject(jsonResult);
      mqttRasa.convertNlu(obj);
    } catch (Exception ex) {
      return false;
    }
    return true;
  }

  private void initMqtt(Map<String, Object> configs, String language)
      throws MqttException {
    ///////////////////////////////////////
    mapper = new JsonMarshaller();
    client = new MqttHandler(configs);
    String lang = language.substring(0, language.indexOf('_')).toLowerCase();

    client.register(ASR_TOPIC + '/' + lang, this::receiveAsr);
    //client.register(NLU_TOPIC + '/' + lang, this::receiveNlu);
    // do I need to subscribe to publish? NO!
    //client.register(OUT_TOPIC);
    ////////////////////////////////////////
  }

  // ------------------ init the Communication Hub -----------------------------------------
  @SuppressWarnings("unchecked")
  public void init(File configDir, Map<String, Object> configs)
          throws IOException, WrongFormatException, MqttException {
    // check that we got the right config
    String checkConfig = (String) configs.get("agentBase");
    if (checkConfig.equals("de.dfki.vondabase.BaseAgent")) {
      _agent = new DialogAgent();
      String language = (String)configs.get("language");
      _agent.init(configDir, configs, language);
      initMqtt((Map<String, Object>)configs.get("mqtt"), language);
    } else {
      throw new IllegalArgumentException("unknown config " + checkConfig);
    }
    registerBehaviourListener(new Listener<Behaviour>() {

      @Override
      public void listen(Behaviour q) {
        Optional<String> out = mapper.marshal(q);
        if (out.isPresent()) {
          client.sendMessage(TTS_TOPIC, out.get());
        } else {
          logger.error("Could not serialize Behaviour: {}", q);
        }
      }

      @Override
      public void free() { }

    });
    _agent.setCommunicationHub(this);
  }

  // --------------------- start/shutdown -----------------------------------
  public void startListening() {
    Thread listenToClient = new Thread() {
      @Override
      public void run() {
        runReceiveSendCycle();
      }
    };
    listenToClient.setName("ListenToEvents");
    listenToClient.setDaemon(true);
    listenToClient.start();
  }

  public void shutdown() {
    // disconnect from communication infrastructure
    try {
      client.disconnect();
    } catch (MqttException e) {
      logger.error("Error disconnecting MQTT: {}", e);
    }
    isRunning = false;
  }

  // --------- register new Listener ----------------------------------------
  public void registerBehaviourListener(Listener<Behaviour> listener) {
    _listeners.add(listener);
  }

  // ------------ publish new Events (Behavior, Dia, RosMessage -----------------------
  public void sendEvent(Object in) {
    inQueue.push(in);
  }

  // depends on the concrete Event class
  private void onEvent(Object evt) {
    logger.debug("on event ...");
    if (evt instanceof Intention) {
      _agent.executeProposal((Intention) evt);
    } else if (evt instanceof DialogueAct) {
      logger.debug("Dia {}", evt);
      _agent.addLastDA((DialogueAct) evt);
      _agent.newData();
    } else if (evt instanceof String) {
      logger.debug("String {}", evt);
      DialogueAct da = _agent.analyse((String) evt);
      sendEvent(da);
    } else if (evt instanceof AsrResult) {
      String text = ((AsrResult)evt).getText();
      logger.debug("AsrResult {}" + text);
      DialogueAct da = _agent.analyse(text);
      da.setValue("sender", _agent.user.toString());
      sendEvent(da);
    } else {
      logger.warn("Unknown incoming object: {}", evt);
    }
  }

  private void runReceiveSendCycle() {
    while (isRunning()) {
      boolean emptyRun = true;
      while (!inQueue.isEmpty()) {
        Object event = inQueue.pollFirst();
        onEvent(event);
      }
      // if a proposal was executed, handle pending events now
      if (!_agent.waitForIntention()) {
        // handle any pending events
        while (!pendingEvents.isEmpty()) {
          onEvent(pendingEvents.removeLast());
        }
        _agent.processRules();
      }
      synchronized (itemsToSend) {
        Object c = itemsToSend.peekFirst();
        if (c != null && (c instanceof Behaviour)
                && _agent.waitForBehaviours((Behaviour) c)) {
          c = null;
        }
        if (c != null) {
          itemsToSend.removeFirst();
          logger.debug("<-- {}", c);
          sendThis(c);
          emptyRun = false;
        }
      }
      if (emptyRun) {
        try {
          Thread.sleep(100);
        } catch (InterruptedException ex) {
          // shut down?
        }
      }
    }
    _agent.shutdown();
  }

  @Override
  public void sendBehaviour(Behaviour b) {
    _listeners.parallelStream().forEach((l) -> {
      l.listen(b);
    });
  }

  // select one of a set of intentions
  @Override
  public void sendIntentions(Set<String> intentions) {
    if (intentions.isEmpty()) return;
    // The following is a stub "statistical" component which randomly selects
    // one intention
    int rand = r.nextInt(intentions.size());
    String intention = null;
    Iterator<String> it = intentions.iterator();
    for (int i = 0; i <= rand; ++i) {
      intention = it.next();
    }
    sendEvent(new Intention(intention, 0.0));
  }

  // Depends on the concrete Event class
  private void sendThis(Object e) {
    if (e instanceof Behaviour)
      sendBehaviour((Behaviour) e);
    else
      logger.warn("Unknown Object to send: {}", e);
  }

  public BaseAgent getAgent() {
    return _agent;
  }

  private boolean isRunning() {
    return isRunning;
  }

  public void sendDA(DialogueAct da) {
    JSONObject json = new JSONObject();
    json.put("intent", da.getDialogueActType());
    String prop = da.getProposition();
    if (prop != null) {
      json.put("proposition", da.getProposition());
    }
    for (String slot : da.getAllSlots()) {
      if (! slot.startsWith("_")) {
        json.put(slot, da.getValue(slot));
      }
    }
    sendMessage(json.toString());
  }

  public void sendMessage(String s) {
    client.sendMessage(OUT_TOPIC, s);
  }
}
