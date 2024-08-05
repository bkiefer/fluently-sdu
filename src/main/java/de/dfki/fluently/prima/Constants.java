package de.dfki.fluently.prima;

public interface Constants {

  //public static final String USER_CLASS = "<dom:Animate>";

  public static final String ROBOT_CLASS = "<soho:Cobot>";
  public static final String ROBOT_URI = "<dom:Robot01>";

  public static final String USER_CLASS = "<cim:User>";
  public static final String USER_URI = "<dom:User01>";
  // MQTT TOPICS

  String IN_TOPIC = "core/messages";
  String ASR_TOPIC = "voskasr/asrresult";
  String NLU_TOPIC = "voskasr/nlu";

  String OUT_TOPIC = "nlu/intent";
  String TTS_TOPIC = "tts/behaviour";

}
