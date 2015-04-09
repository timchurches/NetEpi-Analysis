# vim: set ts=4 sw=4 et:
#
#   The contents of this file are subject to the HACOS License Version 1.2
#   (the "License"); you may not use this file except in compliance with
#   the License.  Software distributed under the License is distributed
#   on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
#   implied. See the LICENSE file for the specific language governing
#   rights and limitations under the License.  The Original Software
#   is "NetEpi Analysis". The Initial Developer of the Original
#   Software is the Health Administration Corporation, incorporated in
#   the State of New South Wales, Australia.
#
#   Copyright (C) 2004,2005 Health Administration Corporation. 
#   All Rights Reserved.
#

import Numeric
import soomfunc
import mx.DateTime
import Search
%%

# A Yapps2 scanner/parser for the SOOM expression language
# (see http://theory.stanford.edu/~amitp/Yapps)

parser soomparse:
    ignore:     '[ \t\n\r]+'
    token END:  '$'
    token DATE: r'\d{4}-\d{1,2}-\d{1,2}'
    token INT:  '[-+]?[0-9]+'
#    token FLOAT:'[-+]?([0-9]*\.)?[0-9]+([eE][-+]?[0-9]+)?'
    # there are three parts to the FLOAT pattern:
    #   [0-9]*\.[0-9]+                          0.1234
    #   [0-9]+\.                                123.
    #   ([0-9]*\.)?[0-9]+[eE][-+]?[0-9]+        0.1e-3
    token FLOAT:'[-+]?([0-9]*\.[0-9]+)|([0-9]+\.)|(([0-9]*\.)?[0-9]+[eE][-+]?[0-9]+)'
    token ID:   '[a-zA-Z0-9_]+' 
    token STR:  '[rR]?\'([^\\n\'\\\\]|\\\\.)*\'|[rR]?"([^\\n"\\\\]|\\\\.)*"'
    token WORD: r"[a-zA-Z0-9'*]?[a-zA-Z0-9][a-zA-Z0-9'*]*"


    rule starts_with: "starting" "with"         {{ return 'op_equal_col' }}
                    | "=:"                      {{ return 'op_equal_col' }}
                    | "==:"                     {{ return 'op_equal_col' }}
                    | "startingwith"            {{ return 'op_equal_col' }}
                    | "startswith"              {{ return 'op_equal_col' }}
                    | "eq:"                     {{ return 'op_equal_col' }}

    rule lt:          "lessthan"                {{ return 'op_less_than' }}
                    | "lt"                      {{ return 'op_less_than' }}
                    | "<"                       {{ return 'op_less_than' }}

    rule lt_col:      "lessthan:"               {{ return 'op_less_than_col' }}
                    | "lt:"                     {{ return 'op_less_than_col' }}
                    | "<:"                      {{ return 'op_less_than_col' }}

    rule le:          "lessthanorequalto"       {{ return 'op_less_equal' }}
                    | "lessequal"               {{ return 'op_less_equal' }}
                    | "le"                      {{ return 'op_less_equal' }}
                    | "<="                      {{ return 'op_less_equal' }}
                    | "=<"                      {{ return 'op_less_equal' }}

    rule le_col:      "lessthanorequalto:"      {{ return 'op_less_equal_col' }}
                    | "lessequal:"              {{ return 'op_less_equal_col' }}
                    | "le:"                     {{ return 'op_less_equal_col' }}
                    | "<=:"                     {{ return 'op_less_equal_col' }}
                    | "=<:"                     {{ return 'op_less_equal_col' }}

    rule lt_clause:   "less" ( "than"   (       {{ return 'op_less_than' }}
                                        | "or" "equal" ("to" {{ return 'op_less_equal' }}
                                                       | "to:" {{ return 'op_less_equal_col' }}
                                                       )
                                        )
                             | "than:" {{ return 'op_less_than_col' }}
                             | "or" ("equal"    {{ return 'op_less_equal' }}
                                    | "equal:"  {{ return 'op_less_equal_col' }}
                                    )
                             )

    rule gt:          "greaterthan"             {{ return 'op_greater_than' }}
                    | "gt"                      {{ return 'op_greater_than' }}
                    | ">"                       {{ return 'op_greater_than' }}

    rule gt_col:      "greaterthan:"            {{ return 'op_greater_than_col' }}
                    | "gt:"                     {{ return 'op_greater_than_col' }}
                    | ">:"                      {{ return 'op_greater_than_col' }}

    rule ge:          "greaterthanorequalto"    {{ return 'op_greater_equal' }}
                    | "greaterequal"            {{ return 'op_greater_equal' }}
                    | "ge"                      {{ return 'op_greater_equal' }}
                    | ">="                      {{ return 'op_greater_equal' }}
                    | "=>"                      {{ return 'op_greater_equal' }}

    rule ge_col:      "greaterthanorequalto:"   {{ return 'op_greater_equal_col' }}
                    | "greaterequal:"           {{ return 'op_greater_equal_col' }}
                    | "ge:"                     {{ return 'op_greater_equal_col' }}
                    | ">=:"                     {{ return 'op_greater_equal_col' }}
                    | "=>:"                     {{ return 'op_greater_equal_col' }}

    rule gt_clause: "greater" ( "than" (        {{ return 'op_greater_than' }}
                                       | "or" "equal" ("to" {{ return 'op_greater_equal' }}
                                                      | "to:" {{ return 'op_greater_equal_col' }}
                                                      )
                                       )
                              | "than:" {{ return 'op_greater_than_col' }}
                              | "or" ("equal"   {{ return 'op_greater_equal' }}
                                     | "equal:" {{ return 'op_greater_equal_col' }}
                                     )
                              )

    rule ne:          "notequalto"              {{ return 'op_not_equal' }}
                    | "notequal"                {{ return 'op_not_equal' }}
                    | "doesnotequal"            {{ return 'op_not_equal' }}
                    | "ne"                      {{ return 'op_not_equal' }}
                    | "!="                      {{ return 'op_not_equal' }}
                    | "!=="                     {{ return 'op_not_equal' }}
                    | "#"                       {{ return 'op_not_equal' }}
                    | "<>"                      {{ return 'op_not_equal' }}

    rule ne_col:      "notequalto:"             {{ return 'op_not_equal_col' }}
                    | "notequal:"               {{ return 'op_not_equal_col' }}
                    | "doesnotequal:"           {{ return 'op_not_equal_col' }}
                    | "ne:"                     {{ return 'op_not_equal_col' }}
                    | "!=:"                     {{ return 'op_not_equal_col' }}
                    | "!==:"                    {{ return 'op_not_equal_col' }}
                    | "#:"                      {{ return 'op_not_equal_col' }}
                    | "<>:"                     {{ return 'op_not_equal_col' }}
                    | "notstartingwith"         {{ return 'op_not_equal_col' }}
                    | "notstartswith"           {{ return 'op_not_equal_col' }}

    rule ne_clause:   "not" ( "equal" (         {{ return 'op_not_equal' }}
                                      | "to"    {{ return 'op_not_equal' }}
                                      | "to:"   {{ return 'op_not_equal_col' }}
                                      )
                            | "equal:"          {{ return 'op_not_equal_col' }}
                            | "starting" "with" {{ return 'op_not_equal_col' }}
                            | "startswith"      {{ return 'op_not_equal_col' }}
                            | "starts" "with"   {{ return 'op_not_equal_col' }}
                            )

    rule does_not_clause: "does" "not" ( "equal" {{ return 'op_not_equal' }}
                                       | "equal:" {{ return 'op_not_equal_col' }}
                                       )

    rule eq:          "equal" "to"              {{ return 'op_equal' }}
                    | "equals"                  {{ return 'op_equal' }}
                    | "equalto"                 {{ return 'op_equal' }}
                    | "eq"                      {{ return 'op_equal' }}
                    | "="                       {{ return 'op_equal' }}
                    | "=="                      {{ return 'op_equal' }}

    # (not called "in" because of conflict in parser with python res word)
    rule in_op:       "in"                      {{ return 'op_in' }}
    
    rule in_col:      "in:"                     {{ return 'op_in_col' }}

    rule not_in:      "notin"                   {{ return 'op_not_in' }}

    rule not_in_col:  "notin:"                  {{ return 'op_not_in_col' }}

    rule between:     "between"                 {{ return 'op_between' }}

    rule contains:    "contains"                {{ return 'op_contains' }}

    rule op:          starts_with               {{ return starts_with }}
                    | lt                        {{ return lt }}
                    | lt_col                    {{ return lt_col }}
                    | lt_clause                 {{ return lt_clause }}
                    | gt                        {{ return gt }}
                    | gt_col                    {{ return gt_col }}
                    | gt_clause                 {{ return gt_clause }}
                    | ge                        {{ return ge }}
                    | ge_col                    {{ return ge_col }}
                    | le                        {{ return le }}
                    | le_col                    {{ return le_col }}
                    | ne                        {{ return ne }}
                    | ne_col                    {{ return ne_col }}
                    | ne_clause                 {{ return ne_clause }}
                    | does_not_clause           {{ return does_not_clause }}
                    | eq                        {{ return eq }}
                    | in_op                     {{ return in_op }}
                    | in_col                    {{ return in_col }}
                    | not_in                    {{ return not_in }}
                    | not_in_col                {{ return not_in_col }}
                    | between                   {{ return between }}
                    | contains                  {{ return contains }}

    rule goal:  expr END                        {{ return expr }}

    # Used for testing the query engine
    rule sgoal: sexpr END                       {{ return sexpr }}

    # An expression is the logical "or" of factors
    rule expr:        factor                    {{ f = factor }}
                      ( "or" factor             {{ f = soomfunc.union(f, factor) }}
                      )*                        {{ return f }}

    # A factor is the logical "and" of comparisons, ("and" has higher precedence than "or")
    rule factor:      comparison                {{ f = comparison }}
                      ( "and" comparison        {{ f = soomfunc.intersect(f, comparison) }}
                      )*                        {{ return f }}

    # A comparison is the comparison of terms
                                                # the real work's done here
    rule comparison:  col op term               {{ return col.filter_op(op, term, self.filter_keys) }}
                    | "\\(" expr "\\)"          {{ return expr }}
                    | "not" comparison          {{ return soomfunc.outersect(Numeric.arrayrange(len(self.dataset)), comparison) }}

    # A term is either a number or an expression surrounded by parentheses
    rule term:        INT                       {{ return int(INT) }}
                    | FLOAT                     {{ return float(FLOAT) }}
                    | STR                       {{ return dequote(STR) }}
                    | "\\[\\[" sexpr "\\]\\]"   {{ return sexpr }}
                    | "\\("
                           ( term               {{ term_list = [term] }}
                            ( "," term          {{ term_list.append(term) }}
                            ) *
                           )+ "\\)"             {{ return term_list }}
                    | "date" 
                      ( "\\(" INT               {{ year = int(INT) }}
                        "," INT                 {{ month = int(INT) }}
                        "," INT                 {{ day = int(INT) }}
                        "\\)"                   {{ return mx.DateTime.Date(year, month, day) }}
                      | DATE                    {{ return mx.DateTime.ISO.ParseDate(DATE) }}
                      )
                                               
                    | "reldate" kwargs          {{ return relativeDate(**kwargs) }}

    rule col:         ID                        {{ return self.dataset.get_column(ID) }}

    # Pythonesque keyword arguments, eg... foo="abc", bah=9
    rule kwargs:    "\\("                       {{ kwargs = {} }}
                      (
                        | ID "=" term           {{ kwargs[ID] = term }}
                          ( "," ID "=" term     {{ kwargs[ID] = term }}
                          ) *
                      )
                    "\\)"                       {{ return kwargs }}

    # a search expression is disjuction of search factors
    rule sexpr:     sfactor                     {{ f = Search.Disjunction(sfactor) }}
                    ( "\\|" sfactor             {{ f.append(sfactor) }}
                    )*                          {{ return f }}

    # a search factor is the conjunction of words, ("and" has higher precedence than "or")
    rule sfactor:   sphrase                     {{ f = sphrase}}
                    (   sconjop sphrase         {{ f = Search.Conjunction(sconjop, f, sphrase) }}
                      | snearop                 {{ op = snearop; nearness = Search.Conjunction.DEFAULT_NEARNESS }}
                        ( "\\[" INT "\\]"       {{ nearness = int(INT) }}
                          | )
                        sphrase                 {{ f = Search.Conjunction(op, f, sphrase, nearness) }}
                      |                         {{ op = '&' }}
                        ( "-"                   {{ op = '&!' }}
                          | )
                        sphrase                 {{ f = Search.Conjunction(op, f, sphrase) }}
                    )*                          {{ return f }}

    # search conjunction operations: and, and not
    rule sconjop:   ( "&"                       {{ op = '&' }}
                      ( "-"                     {{ op = '&!' }}
                        | )
                    )                           {{ return op }}

    # search proximity operations: before, after, near
    rule snearop:     "<"                       {{ return '<' }}
                    | ">"                       {{ return '>' }}
                    | "~"                       {{ return '~' }}

    # a search phrase is a single word or a phrase or word expressions
    rule sphrase:     sterm                     {{ return sterm }}
                    | "\""                      {{ words = [] }}
                      ( sterm                   {{ words.append(sterm) }}
                      )+
                      "\""                      {{ return Search.Phrase(words) }}

    # a search term is a single word or a sub-expression
    rule sterm:       WORD                      {{ return Search.Word(WORD) }}
                    | "\\(" sexpr "\\)"         {{ return sexpr }}

%%

import re
dequote_re = re.compile(r'\\(x[0-9a-fA-F]{2}|[0-7]{1,3}|.)')
backslash_map = {
    '\\': '\\', 
    "'": "'",
    '"': '"', 
    'a': '\a', 
    'b': '\b', 
    'f': '\f', 
    'n': '\n', 
    'r': '\r', 
    't': '\t', 
    'v': '\v', 
}
def dequote(s):
    """
    Remove leading and trailing quotes, honour any backslash quoting
    within the string.

    Using the built-in eval() looks attractive at first glance, but
    opens serious security issues.
    """
    def backslash_sub(match):
        match = match.group(0)
        if match.startswith(r'\x'):
            try:
                return chr(int(match[2:], 16))
            except ValueError:
                raise ValueError('invalid \\x escape')
        elif match[1:].isdigit():
            return chr(int(match[1:], 8))
        else:
            return backslash_map.get(match[1:], match)
    if s[0] in ('r', 'R'):
        return s[2:-1]
    return dequote_re.sub(backslash_sub, s[1:-1])

def relativeDate(years=None, months=None, days=None, align=None):
    def onlyone():
        raise ValueError('Only specify one of years, months, or days')
    weekdays = {
        'monday': mx.DateTime.Monday,
        'tuesday': mx.DateTime.Tuesday,
        'wednesday': mx.DateTime.Wednesday,
        'thursday': mx.DateTime.Thursday,
        'friday': mx.DateTime.Friday,
        'saturday': mx.DateTime.Saturday,
        'sunday': mx.DateTime.Sunday,
    }
    kwargs = {
        'hour': 0,
        'minute': 0,
        'second': 0,
    }
    if years:
        if months or days:
            onlyone()
        kwargs['years'] = years
    elif months:
        if days:
            onlyone()
        kwargs['months'] = months
    elif days:
        kwargs['days'] = days
    if align:
        weekday = weekdays.get(align.lower())
        if weekday is not None:
            kwargs['weekday'] = weekday, 0
        elif align.lower() in ('bom', '1st', 'som'):
            kwargs['day'] = 1
        elif align.lower() in ('boy', 'soy'):
            kwargs['day'] = 1
            kwargs['month'] = mx.DateTime.January
        else:
            raise ValueError('bad relative date alignment %r' % align)
    return mx.DateTime.now() + mx.DateTime.RelativeDateTime(**kwargs)

class SoomFilterParse(soomparse):
    def __init__(self, dataset, expr, filter_keys=()):
        self.dataset = dataset
        self.filter_keys = filter_keys
        self.__expr = expr
        soomparse.__init__(self, soomparseScanner(expr))
        self.__filter = wrap_error_reporter(self, 'goal')

    def filter(self):
        # XXX probably want to build the return type here
#       print 'SoomFilterParse.filter: f("%s") %s' % (self.__expr, self.__filter)
        return self.__filter
