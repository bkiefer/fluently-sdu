package de.dfki.mlt.actionconv;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.IOException;
import java.io.StringReader;

import org.junit.Test;

public class FormulaTest {

  @Test
  public void test() throws IOException {
    String input = "A & (B | !(D | ! E | (!(F & G)) | H)) | I";
    CondParser p = new CondParser(new Lexer(new StringReader(input)));
    assertTrue(p.parse());
    Formula f = p.cond;
    f.pushDownNeg();
    f.flattenStrata();
    assertEquals("((A & (B | (!D & E & F & G & !H))) | I)", f.toString());
  }

  @Test
  public void test1() throws IOException {
    String input = "B | (!D & E & (F & G) & !H)";
    CondParser p = new CondParser(new Lexer(new StringReader(input)));
    assertTrue(p.parse());
    Formula f = p.cond;
    f.flattenStrata();
    assertEquals("(B | (!D & E & F & G & !H))", f.toString());
  }


  @Test
  public void test2() throws IOException {
    String input = "(!D & E & !(F | !G) & !H)";
    CondParser p = new CondParser(new Lexer(new StringReader(input)));
    assertTrue(p.parse());
    Formula f = p.cond;
    f.pushDownNeg();
    f.flattenStrata();
    assertEquals("(!D & E & !F & G & !H)", f.toString());
  }
}
