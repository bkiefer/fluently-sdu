package de.dfki.mlt.actionconv;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.IOException;
import java.io.StringReader;

import org.junit.Test;

public class FormulaTest {

  String[] formulae = {
      "A & (B | !(D | ! E | (!(F & G)) | H)) | I",
      "B | (!D & E & (F & G) & !H)",
      "(!D & E & !(F | !G) & !H)",
      "(A & C & (!A | B))",
      "(A & C & (!A | B | C))",
      "(A | B) & (D | E) & (F | G)",
      "A & B",
      "A | B",
      "!(A & B)",
      "!(A | B)",
      "A",
      "!A"
  };

  String [] dnfs = {
      "((A & B) | (A & !D & E & F & G & !H) | I)",
      "(B | (!D & E & F & G & !H))",
      "(!D & E & !F & G & !H)",
      "(A & B & C)",
      "((A & B & C) | (A & C))",
      "((A & D & F) | (A & D & G) | (A & E & F) | (A & E & G) | (B & D & F) | (B & D & G) | (B & E & F) | (B & E & G))",
      "(A & B)",
      "(A | B)",
      "(!A | !B)",
      "(!A & !B)",
      "A",
      "!A"
  };

  @Test
  public void test() throws IOException {
    CondParser p = new CondParser(new Lexer(new StringReader(formulae[0])));
    assertTrue(p.parse());
    Formula f = p.cond;
    f.pushDownNeg();
    assertEquals("((A & (B | (!D & E & (F & G) & !H))) | I)", f.toString());
    f.flattenStrata();
    assertEquals("((A & (B | (!D & E & F & G & !H))) | I)", f.toString());
  }

  @Test
  public void test1() throws IOException {
    CondParser p = new CondParser(new Lexer(new StringReader(formulae[1])));
    assertTrue(p.parse());
    Formula f = p.cond;
    f.flattenStrata();
    assertEquals("(B | (!D & E & F & G & !H))", f.toString());
  }


  @Test
  public void test2() throws IOException {
    CondParser p = new CondParser(new Lexer(new StringReader(formulae[2])));
    assertTrue(p.parse());
    Formula f = p.cond;
    f.pushDownNeg();
    f.flattenStrata();
    assertEquals("(!D & E & !F & G & !H)", f.toString());
  }

  @Test
  public void testDnf() throws IOException {
    int i = 0;
    for (String form: formulae) {
      CondParser p = new CondParser(new Lexer(new StringReader(form)));
      assertTrue(p.parse());
      Formula f = p.cond;
      f.pushDownNeg();
      Formula dnf = f.constructDnf();
      //System.out.println(dnf);
      assertEquals(dnfs[i++], dnf.toString());
    }
  }
}
