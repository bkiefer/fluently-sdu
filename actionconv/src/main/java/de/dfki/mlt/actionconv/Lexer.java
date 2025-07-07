package de.dfki.mlt.actionconv;

import java.io.IOException;
import java.io.Reader;
import java.util.HashMap;


public class Lexer implements CondParser.Lexer {
  private static String[] tokenNames = {
    "BASIC"
  };

  private static final int ID_TOKEN = 258;

  private static final String charTokens = "&|!()";

  private int _pushBack = -1;

  private Reader _in;

  private int _nextChar;

  private String _lval;

  private int _line, _column;

  private HashMap<Integer, String> token2String;

  private Lexer() {
    token2String = new HashMap<Integer, String>();
    for (int i = 0; i < charTokens.length(); ++i) {
      char c = charTokens.charAt(i);
      token2String.put(((int) c),  Character.toString(c));
    }

    for (int i = 0; i < tokenNames.length; ++i) {
      token2String.put(ID_TOKEN + i, tokenNames[i]);
    }
    _in = null;
  }

  public Lexer(Reader in) {
    this();
    setInputReader(in);
  }

  public void setInputReader(Reader in) {
    _in = in;
    _line = 1;
    _column = 0;
    _nextChar = ' ';
  }

  /** for lexer debugging purposes */
  public String getTokenName(int token) {
    return token2String.get(token);
  }

  /* We have our own position tracking
  public Position getStartPos() { return new Position(); }
  public Position getEndPos() { return new Position(); }
  */


  @Override
  public void yyerror (String msg) {
    System.out.println(msg + " in [" + _line + "," + _column + "]");
  }

  void skipws() throws IOException {
    do {
      while (_nextChar == ' ') {
        readNext();
      }
    } while (_nextChar == ' ');
  }

  @SuppressWarnings("fallthrough")
  private void readNext() throws IOException {
    if (_pushBack >= 0) {
      _nextChar = _pushBack;
      _pushBack = -1;
    } else {
      _nextChar = _in.read();
    }
    ++_column;
    switch (_nextChar) {
    case -1: _nextChar = CondParser.Lexer.EOF; break;
    case '\n': _column = 0; ++_line; // fall through is intended
    case ' ':
    case '\t':
    case '\u000C':_nextChar = ' ' ; break;
    case '\r':
      _column = 0; ++_line;
      _nextChar = _in.read();
      if (_nextChar != '\n')
        _pushBack = _nextChar;
      _nextChar = ' ';
      break;
    }
  }

  public String readLine() throws IOException {
    StringBuilder sb = new StringBuilder();
    int currentLine = _line;
    skipws();
    while (_nextChar != CondParser.Lexer.EOF && _line == currentLine) {
      sb.append((char) _nextChar);
      readNext();
    }
    return sb.toString();
  }

  public int peek() throws IOException {
    skipws();
    return _nextChar;
  }

  public int peekFollowing() throws IOException {
    _pushBack = _in.read();
    return _pushBack;
  }

  public boolean atEOF() {
    return _nextChar == CondParser.Lexer.EOF;
  }

  /*
    --------- Tokens:
    BASIC     [a-zA-Z][-_a-zA-Z0-9]*
    // STRING "([^\\"]|\\")*"

    --------- single-char tokens
    CONJ   &
    ALT    |
    OPAREN (
    CPAREN )
    NOT    !
  */

  @Override
  public int yylex () throws java.io.IOException {
    _lval = null;
    skipws();
    switch (_nextChar) {
    case CondParser.Lexer.EOF:
    case '(':
    case ')':
    case '&':
    case '|':
    case '!': {
      int result = _nextChar;
      readNext();
      return result;
    }}
    /*
    case '"': {
      StringBuffer sb = new StringBuffer();
      readNext();
      while (_nextChar != '"') {
        if (_nextChar == '\\') {
          readNext();
        }
        if (_nextChar == CondParser.Lexer.EOF) {
          yyerror("unexpected end of input in string");
          return CondParser.Lexer.EOF;
        }
        sb.append((char) _nextChar);
        readNext();
      }
      readNext();
      _lval = sb.toString();
      return CondParser.Lexer.STRING;
    }*/

    StringBuffer sb = new StringBuffer();
    while (Character.isLetterOrDigit(_nextChar)
        || _nextChar == '-' || _nextChar == '_' || _nextChar == '\''
        || _nextChar == '+') {
      sb.append((char) _nextChar);
      readNext();
    }
    _lval = sb.toString();
    if (_lval.isEmpty()) {
      yyerror("Empty identifier, possibly illegal character");
      readNext();
    }
    return CondParser.Lexer.BASIC;
  }

  @Override
  public Object getLVal () {
    return _lval;
  }

}
