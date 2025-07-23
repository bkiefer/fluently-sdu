package de.dfki.mlt.actionconv;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.Iterator;
import java.util.List;

public class Formula {
  boolean neg = false;
  List<Formula> subs = null;
  char what = 'l';
  String code = null;

  private Formula(char w, List<Formula> s) {
    what = w;
    subs = s;
  }

  private Formula(String c) {
    code = c;
  }

  private Formula(char w, Formula left, Formula right) {
    what = w;
    subs = new ArrayList<>();
    subs.add(left);
    subs.add(right);
  }

  /** Only for literals!!! */
  private Formula cloneLiteral() {
    Formula res = new Formula(code);
    res.neg = neg;
    return res;
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

  public static Formula createDisj(Formula left, Formula right) {
    return create('d', left, right);
  }

  public static Formula createConj(Formula left, Formula right) {
    return create('c', left, right);
  }

  public static Formula createNeg(Formula f) {
    f.neg = ! f.neg;
    return f;
  }

  public static Formula createBasic(String code) {
    return new Formula(code);
  }

  void pushDownNeg() {
    if (subs == null) return;
    if (neg) {
      for (Formula sub: subs) {
        sub.neg = ! sub.neg;
      }
      neg = !neg;
      what = (what == 'c' ? 'd' : 'c');
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

  private void addSubs(List<Formula> l, Formula f) {
    if (f.subs == null) {
      l.add(f);
    } else {
      l.addAll(f.subs);
    }
  }

  private Formula disjunctionExpansion(List<Formula> disj) {
    if (disj.size() == 1) {
      return disj.get(0);
    }
    Formula first = disj.get(0);
    Formula rest = disjunctionExpansion(disj.subList(1, disj.size()));
    List<Formula> newconjs = new ArrayList<>();
    for (Formula fconj: first.subs) {
      for (Formula rconj: rest.subs) {
        List<Formula> newsubs = new ArrayList<>();
        addSubs(newsubs, fconj);
        addSubs(newsubs, rconj);
        // create new conj with newconj as subs
        Formula newconj = new Formula('c', newsubs);
        newconjs.add(newconj);
      }
    }
    first.subs = newconjs;
    return first;
  }

  private Formula createDNF() {
    Formula newdisj = this;
    switch (what) {
    case 'l': break;
    case 'd' :
      List<Formula> newsubs = new ArrayList<>();
      for (Formula sub: subs) {
        Formula newSub = sub.createDNF();
        addSubs(newsubs, newSub);
      }
      this.subs = newsubs;
      break;
    case 'c' :
      // collect all direct literals
      List<Formula> literals = new ArrayList<>();
      List<Formula> disjunctions = new ArrayList<>();
      for (Formula sub: subs) {
        if (sub.what == 'l') {
          literals.add(sub);
        } else {
          disjunctions.add(sub.createDNF());
        }
      }
      if (disjunctions.isEmpty()) {
        List<Formula> newconjs = new ArrayList<>();
        newconjs.add(this);
        newdisj = new Formula('d', newconjs);
      } else {
        newdisj = disjunctionExpansion(disjunctions);
        for (Formula c: newdisj.subs) {
          if (c.subs == null) {
            List<Formula> newconjs = new ArrayList<>();
            Formula newLiteral = c.cloneLiteral();
            newconjs.add(newLiteral);
            newconjs.addAll(literals);
            c.what = 'c';
            c.neg = false;
            c.code = null;
            c.subs = newconjs;
          } else {
            // append the literals to all conjuncts in the result
            c.subs.addAll(literals);
          }
        }
        break;
      }
    }
    return newdisj;
  }

  private class CodeComparator implements Comparator<Formula> {
    @Override
    public int compare(Formula o1, Formula o2) {
      return o1.code.compareTo(o2.code);
    }
  }

  private void compactDNF() {
    if (subs == null) return;
    Iterator<Formula> cit = subs.iterator();
    while (cit.hasNext()) {
      Formula conj = cit.next();
      if (conj.subs != null) {
        conj.subs.sort(new CodeComparator());
        Iterator<Formula> lit = conj.subs.iterator();
        Formula last = lit.next();
        while (lit.hasNext()) {
          Formula now = lit.next();
          if (last.code.equals(now.code)) {
            if (last.neg == now.neg) {
              lit.remove(); // same literal twice
            } else {
              cit.remove(); // inconsistent a & !a
              break;
            }
          } else {
            last = now;
          }
        }
      }
    }

  }


  public Formula constructDnf() {
    pushDownNeg();    // push negations to the literals
    flattenStrata();  // now there's a sequence of conj only and disj only
    Formula res = createDNF();  // construct DNF
    // do compaction: equal literals or inconsistent conjunctions: (a & !a)
    res.compactDNF();
    if (res.subs != null && res.subs.size() == 1)
      // return the conjunction in case there is only one element
      res = res.subs.get(0);
    return res;
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
