/* -*- Mode: Java -*- */

%code imports {

import java.io.Reader;
import java.util.*;
import de.dfki.mlt.memactions.Main;
import org.semanticweb.owlapi.model.OWLNamedIndividual;

@SuppressWarnings({"serial", "unchecked", "fallthrough", "unused"})
}

%language "Java"

//                       %locations

%define api.package "de.dfki.mlt.memactions"

%define api.parser.public

%define api.parser.class {CondParser}

%define parse.error verbose

%type <OWLNamedIndividual> conj disj unary basic

%code {

public Main main;

public OWLNamedIndividual _cond;

}

%token < String > BASIC

%%

// start rule
start: disj { _cond = $1; };

disj
   : disj  '|' conj { $$ = main.createDisj($1, $3); }
   | conj { $$ = $1; }
   ;

conj
   : conj '&' unary { $$ = main.createConj($1, $3); }
   | unary { $$ = $1; }
   ;


unary
   : '!' basic { $$ = main.createNeg($2); }
   | basic { $$ = $1; }
   ;

basic
   : BASIC { $$ = main.createBasic($1); }
   | '(' disj ')' { $$ = $2; }
