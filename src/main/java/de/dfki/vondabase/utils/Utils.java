package de.dfki.vondabase.utils;

import de.dfki.lt.hfc.types.XsdDouble;
import de.dfki.lt.hfc.types.XsdFloat;

public class Utils {

  public static String float2xsd(Float f) {
    return new XsdFloat(getDefault(f)).toString();
  }

  public static String double2xsd(Double f) {
    return new XsdDouble(getDefault(f)).toString();
  }

  // --------------------- Getter ---------------------------------
  public static float getDefault(Float d) {
    if (d == null) return 0.0f;
    return d;
  }

  public static double getDefault(Double d) {
    if (d == null) return 0.0;
    return d;
  }

  public static int getDefault(Integer d) {
    if (d == null) return 0;
    return d;
  }

  public static boolean getDefault(Boolean b) {
    if (b == null) return false;
    return b;
  }

}
