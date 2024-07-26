package de.dfki.vondabase.utils;

public interface Listener<T> {
  public void listen(T q);


  void free();
}