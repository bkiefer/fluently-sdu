package de.dfki.fluently.prima.utils;

public interface Listener<T> {
  public void listen(T q);


  void free();
}