/* -*- Mode: Java -*- */

%code imports {

import java.io.Reader;
import java.util.*;
import de.dfki.mlt.actionconv.Formula;

@SuppressWarnings({"fallthrough", "unused"})
}

%language "Java"

//                       %locations

%define api.package "de.dfki.mlt.actionconv"

%define api.parser.public

%define api.parser.class {CondParser}

%define parse.error verbose

%type <Formula> conj disj unary basic

%code {

public Formula cond;

}

%token < String > BASIC

%%

// start rule
start: disj { cond = $1; };

disj
   : disj  '|' conj { $$ = Formula.createDisj($1, $3); }
   | conj { $$ = $1; }
   ;

conj
   : conj '&' unary { $$ = Formula.createConj($1, $3); }
   | unary { $$ = $1; }
   ;

unary
   : '!' basic { $$ = Formula.createNeg($2); }
   | basic { $$ = $1; }
   ;

basic
   : BASIC { $$ = Formula.createBasic($1); }
   | '(' disj ')' { $$ = $2; }
