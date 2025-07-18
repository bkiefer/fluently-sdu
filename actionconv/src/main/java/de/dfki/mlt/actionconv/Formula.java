package de.dfki.mlt.actionconv;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class Formula {
  boolean neg = false;
  List<Formula> subs = null;
  char what = 'l';
  String code = null;

  public Formula(String c) {
    code = c;
  }

  public Formula(char w, Formula left, Formula right) {
    what = w;
    subs = new ArrayList<>();
    subs.add(left);
    subs.add(right);
  }

  private static Formula create(char w, Formula left, Formula right) {
    Formula result = null;
    if (left.what == w) {
      result = left;
      result.subs.add(right);
    } else {
      result = new Formula(w, left, right);
    }
    return result;
  }

  static Formula createDisj(Formula left, Formula right) {
    return create('d', left, right);
  }

  static Formula createConj(Formula left, Formula right) {
    return create('c', left, right);
  }

  static Formula createNeg(Formula f) {
    f.neg = ! f.neg;
    return f;
  }

  static Formula createBasic(String code) {
    return new Formula(code);
  }

  void pushDownNeg() {
    if (subs == null) return;
    if (neg) {
      for (Formula sub: subs) {
        sub.neg = ! sub.neg;
      }
      neg = !neg;
      what = what == 'c' ? 'd' : 'c';
    }
    for (Formula sub: subs) {
      sub.pushDownNeg();
    }
  }

  void flattenStrata() {
    if (subs != null) {
      boolean change;
      List<Formula> newsubs = new ArrayList<>();
      do {
        change = false;
        for (Formula sub: subs) {
          if (what == sub.what) {
            newsubs.addAll(sub.subs);
            change = true;
          } else {
            newsubs.add(sub);
          }
        }
        List<Formula> swap = subs;
        subs = newsubs;
        newsubs = swap; newsubs.clear();
      } while (change);
      for (Formula sub: subs) {
        sub.flattenStrata();
      }
    }
  }

  void createDNF() {

  }

  @Override
  public String toString() {
    String op = "";
    switch (what) {
    case 'l' : return neg ? '!' + code : code;
    case 'd' : op = " | "; break;
    case 'c' : op = " & "; break;
    }
    Iterator<Formula> it = subs.iterator();
    StringBuffer sb = new StringBuffer();
    if (neg) sb.append('!');
    sb.append('(');
    sb.append(it.next().toString());
    while (it.hasNext()) {
      sb.append(op).append(it.next());
    }
    sb.append(')');
    return sb.toString();
  }

}
