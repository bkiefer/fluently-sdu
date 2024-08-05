package de.dfki.fluently.prima.utils;


import de.dfki.mlt.rudimant.agent.Behaviour;
import de.dfki.mlt.rudimant.agent.nlp.DialogueAct;

public class ExtendedBehaviour extends Behaviour {


    private final DialogueAct _intent;
    private final String _dialogueAct;

    public ExtendedBehaviour(final String id, final String text, final String motion, final int delay,
            final DialogueAct intent) {
        super(id, text, motion, delay);
        _intent = intent;
        _dialogueAct = intent.toString();
    }

    public ExtendedBehaviour(final String text, final String motion, final DialogueAct intent) {
        super(text, motion);
        _intent = intent;
        _dialogueAct = intent.toString();
    }

    public ExtendedBehaviour(final String text, final String motion, final int delay, final DialogueAct intent) {
        super(text, motion, delay);
        _intent = intent;
        _dialogueAct = intent.toString();
    }

    @Override
    public String toString() {
        final StringBuilder strb = new StringBuilder("{");
        strb.append("\"behavior\" : { ");
        strb.append("\"id\" : \"" + super.getId() + "\",\n");
        strb.append("\"text\" : \"" + super.getText() + "\",\n");
        strb.append("\"motion\" : \"" + super.getMotion() + "\",\n");
        strb.append("\"delay\" : " + super.getDelay() +"\n");
        strb.append("},\n");
        strb.append("\"dialogueAct\" :  \"" + _intent.toString().replace("\"", "\\\"") + "\"");
        strb.append("}");
        return strb.toString();
    }

    public String getDialogueAct(){
        return _dialogueAct;
    }


}
