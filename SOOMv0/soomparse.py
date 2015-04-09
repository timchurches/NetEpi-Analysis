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

from string import *
import re
from yappsrt import *

class soomparseScanner(Scanner):
    patterns = [
        ('"\\""', re.compile('"')),
        ('"~"', re.compile('~')),
        ('"&"', re.compile('&')),
        ('"-"', re.compile('-')),
        ('"\\\\]"', re.compile('\\]')),
        ('"\\\\["', re.compile('\\[')),
        ('"\\\\|"', re.compile('\\|')),
        ('"reldate"', re.compile('reldate')),
        ('"date"', re.compile('date')),
        ('","', re.compile(',')),
        ('"\\\\]\\\\]"', re.compile('\\]\\]')),
        ('"\\\\[\\\\["', re.compile('\\[\\[')),
        ('"\\\\)"', re.compile('\\)')),
        ('"\\\\("', re.compile('\\(')),
        ('"and"', re.compile('and')),
        ('"contains"', re.compile('contains')),
        ('"between"', re.compile('between')),
        ('"notin:"', re.compile('notin:')),
        ('"notin"', re.compile('notin')),
        ('"in:"', re.compile('in:')),
        ('"in"', re.compile('in')),
        ('"=="', re.compile('==')),
        ('"="', re.compile('=')),
        ('"eq"', re.compile('eq')),
        ('"equalto"', re.compile('equalto')),
        ('"equals"', re.compile('equals')),
        ('"does"', re.compile('does')),
        ('"starts"', re.compile('starts')),
        ('"not"', re.compile('not')),
        ('"notstartswith"', re.compile('notstartswith')),
        ('"notstartingwith"', re.compile('notstartingwith')),
        ('"<>:"', re.compile('<>:')),
        ('"#:"', re.compile('#:')),
        ('"!==:"', re.compile('!==:')),
        ('"!=:"', re.compile('!=:')),
        ('"ne:"', re.compile('ne:')),
        ('"doesnotequal:"', re.compile('doesnotequal:')),
        ('"notequal:"', re.compile('notequal:')),
        ('"notequalto:"', re.compile('notequalto:')),
        ('"<>"', re.compile('<>')),
        ('"#"', re.compile('#')),
        ('"!=="', re.compile('!==')),
        ('"!="', re.compile('!=')),
        ('"ne"', re.compile('ne')),
        ('"doesnotequal"', re.compile('doesnotequal')),
        ('"notequal"', re.compile('notequal')),
        ('"notequalto"', re.compile('notequalto')),
        ('"greater"', re.compile('greater')),
        ('"=>:"', re.compile('=>:')),
        ('">=:"', re.compile('>=:')),
        ('"ge:"', re.compile('ge:')),
        ('"greaterequal:"', re.compile('greaterequal:')),
        ('"greaterthanorequalto:"', re.compile('greaterthanorequalto:')),
        ('"=>"', re.compile('=>')),
        ('">="', re.compile('>=')),
        ('"ge"', re.compile('ge')),
        ('"greaterequal"', re.compile('greaterequal')),
        ('"greaterthanorequalto"', re.compile('greaterthanorequalto')),
        ('">:"', re.compile('>:')),
        ('"gt:"', re.compile('gt:')),
        ('"greaterthan:"', re.compile('greaterthan:')),
        ('">"', re.compile('>')),
        ('"gt"', re.compile('gt')),
        ('"greaterthan"', re.compile('greaterthan')),
        ('"equal:"', re.compile('equal:')),
        ('"than:"', re.compile('than:')),
        ('"to:"', re.compile('to:')),
        ('"to"', re.compile('to')),
        ('"equal"', re.compile('equal')),
        ('"or"', re.compile('or')),
        ('"than"', re.compile('than')),
        ('"less"', re.compile('less')),
        ('"=<:"', re.compile('=<:')),
        ('"<=:"', re.compile('<=:')),
        ('"le:"', re.compile('le:')),
        ('"lessequal:"', re.compile('lessequal:')),
        ('"lessthanorequalto:"', re.compile('lessthanorequalto:')),
        ('"=<"', re.compile('=<')),
        ('"<="', re.compile('<=')),
        ('"le"', re.compile('le')),
        ('"lessequal"', re.compile('lessequal')),
        ('"lessthanorequalto"', re.compile('lessthanorequalto')),
        ('"<:"', re.compile('<:')),
        ('"lt:"', re.compile('lt:')),
        ('"lessthan:"', re.compile('lessthan:')),
        ('"<"', re.compile('<')),
        ('"lt"', re.compile('lt')),
        ('"lessthan"', re.compile('lessthan')),
        ('"eq:"', re.compile('eq:')),
        ('"startswith"', re.compile('startswith')),
        ('"startingwith"', re.compile('startingwith')),
        ('"==:"', re.compile('==:')),
        ('"=:"', re.compile('=:')),
        ('"with"', re.compile('with')),
        ('"starting"', re.compile('starting')),
        ('[ \t\n\r]+', re.compile('[ \t\n\r]+')),
        ('END', re.compile('$')),
        ('DATE', re.compile('\\d{4}-\\d{1,2}-\\d{1,2}')),
        ('INT', re.compile('[-+]?[0-9]+')),
        ('FLOAT', re.compile('[-+]?([0-9]*\\.[0-9]+)|([0-9]+\\.)|(([0-9]*\\.)?[0-9]+[eE][-+]?[0-9]+)')),
        ('ID', re.compile('[a-zA-Z0-9_]+')),
        ('STR', re.compile('[rR]?\'([^\\n\'\\\\]|\\\\.)*\'|[rR]?"([^\\n"\\\\]|\\\\.)*"')),
        ('WORD', re.compile("[a-zA-Z0-9'*]?[a-zA-Z0-9][a-zA-Z0-9'*]*")),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['[ \t\n\r]+'],str)

class soomparse(Parser):
    def starts_with(self):
        _token_ = self._peek('"starting"', '"=:"', '"==:"', '"startingwith"', '"startswith"', '"eq:"')
        if _token_ == '"starting"':
            self._scan('"starting"')
            self._scan('"with"')
            return 'op_equal_col'
        elif _token_ == '"=:"':
            self._scan('"=:"')
            return 'op_equal_col'
        elif _token_ == '"==:"':
            self._scan('"==:"')
            return 'op_equal_col'
        elif _token_ == '"startingwith"':
            self._scan('"startingwith"')
            return 'op_equal_col'
        elif _token_ == '"startswith"':
            self._scan('"startswith"')
            return 'op_equal_col'
        else:# == '"eq:"'
            self._scan('"eq:"')
            return 'op_equal_col'

    def lt(self):
        _token_ = self._peek('"lessthan"', '"lt"', '"<"')
        if _token_ == '"lessthan"':
            self._scan('"lessthan"')
            return 'op_less_than'
        elif _token_ == '"lt"':
            self._scan('"lt"')
            return 'op_less_than'
        else:# == '"<"'
            self._scan('"<"')
            return 'op_less_than'

    def lt_col(self):
        _token_ = self._peek('"lessthan:"', '"lt:"', '"<:"')
        if _token_ == '"lessthan:"':
            self._scan('"lessthan:"')
            return 'op_less_than_col'
        elif _token_ == '"lt:"':
            self._scan('"lt:"')
            return 'op_less_than_col'
        else:# == '"<:"'
            self._scan('"<:"')
            return 'op_less_than_col'

    def le(self):
        _token_ = self._peek('"lessthanorequalto"', '"lessequal"', '"le"', '"<="', '"=<"')
        if _token_ == '"lessthanorequalto"':
            self._scan('"lessthanorequalto"')
            return 'op_less_equal'
        elif _token_ == '"lessequal"':
            self._scan('"lessequal"')
            return 'op_less_equal'
        elif _token_ == '"le"':
            self._scan('"le"')
            return 'op_less_equal'
        elif _token_ == '"<="':
            self._scan('"<="')
            return 'op_less_equal'
        else:# == '"=<"'
            self._scan('"=<"')
            return 'op_less_equal'

    def le_col(self):
        _token_ = self._peek('"lessthanorequalto:"', '"lessequal:"', '"le:"', '"<=:"', '"=<:"')
        if _token_ == '"lessthanorequalto:"':
            self._scan('"lessthanorequalto:"')
            return 'op_less_equal_col'
        elif _token_ == '"lessequal:"':
            self._scan('"lessequal:"')
            return 'op_less_equal_col'
        elif _token_ == '"le:"':
            self._scan('"le:"')
            return 'op_less_equal_col'
        elif _token_ == '"<=:"':
            self._scan('"<=:"')
            return 'op_less_equal_col'
        else:# == '"=<:"'
            self._scan('"=<:"')
            return 'op_less_equal_col'

    def lt_clause(self):
        self._scan('"less"')
        _token_ = self._peek('"than"', '"than:"', '"or"')
        if _token_ == '"than"':
            self._scan('"than"')
            _token_ = self._peek('"or"', 'INT', 'FLOAT', 'STR', '"\\\\[\\\\["', '"\\\\("', '"date"', '"reldate"')
            if _token_ != '"or"':
                return 'op_less_than'
            else:# == '"or"'
                self._scan('"or"')
                self._scan('"equal"')
                _token_ = self._peek('"to"', '"to:"')
                if _token_ == '"to"':
                    self._scan('"to"')
                    return 'op_less_equal'
                else:# == '"to:"'
                    self._scan('"to:"')
                    return 'op_less_equal_col'
        elif _token_ == '"than:"':
            self._scan('"than:"')
            return 'op_less_than_col'
        else:# == '"or"'
            self._scan('"or"')
            _token_ = self._peek('"equal"', '"equal:"')
            if _token_ == '"equal"':
                self._scan('"equal"')
                return 'op_less_equal'
            else:# == '"equal:"'
                self._scan('"equal:"')
                return 'op_less_equal_col'

    def gt(self):
        _token_ = self._peek('"greaterthan"', '"gt"', '">"')
        if _token_ == '"greaterthan"':
            self._scan('"greaterthan"')
            return 'op_greater_than'
        elif _token_ == '"gt"':
            self._scan('"gt"')
            return 'op_greater_than'
        else:# == '">"'
            self._scan('">"')
            return 'op_greater_than'

    def gt_col(self):
        _token_ = self._peek('"greaterthan:"', '"gt:"', '">:"')
        if _token_ == '"greaterthan:"':
            self._scan('"greaterthan:"')
            return 'op_greater_than_col'
        elif _token_ == '"gt:"':
            self._scan('"gt:"')
            return 'op_greater_than_col'
        else:# == '">:"'
            self._scan('">:"')
            return 'op_greater_than_col'

    def ge(self):
        _token_ = self._peek('"greaterthanorequalto"', '"greaterequal"', '"ge"', '">="', '"=>"')
        if _token_ == '"greaterthanorequalto"':
            self._scan('"greaterthanorequalto"')
            return 'op_greater_equal'
        elif _token_ == '"greaterequal"':
            self._scan('"greaterequal"')
            return 'op_greater_equal'
        elif _token_ == '"ge"':
            self._scan('"ge"')
            return 'op_greater_equal'
        elif _token_ == '">="':
            self._scan('">="')
            return 'op_greater_equal'
        else:# == '"=>"'
            self._scan('"=>"')
            return 'op_greater_equal'

    def ge_col(self):
        _token_ = self._peek('"greaterthanorequalto:"', '"greaterequal:"', '"ge:"', '">=:"', '"=>:"')
        if _token_ == '"greaterthanorequalto:"':
            self._scan('"greaterthanorequalto:"')
            return 'op_greater_equal_col'
        elif _token_ == '"greaterequal:"':
            self._scan('"greaterequal:"')
            return 'op_greater_equal_col'
        elif _token_ == '"ge:"':
            self._scan('"ge:"')
            return 'op_greater_equal_col'
        elif _token_ == '">=:"':
            self._scan('">=:"')
            return 'op_greater_equal_col'
        else:# == '"=>:"'
            self._scan('"=>:"')
            return 'op_greater_equal_col'

    def gt_clause(self):
        self._scan('"greater"')
        _token_ = self._peek('"than"', '"than:"', '"or"')
        if _token_ == '"than"':
            self._scan('"than"')
            _token_ = self._peek('"or"', 'INT', 'FLOAT', 'STR', '"\\\\[\\\\["', '"\\\\("', '"date"', '"reldate"')
            if _token_ != '"or"':
                return 'op_greater_than'
            else:# == '"or"'
                self._scan('"or"')
                self._scan('"equal"')
                _token_ = self._peek('"to"', '"to:"')
                if _token_ == '"to"':
                    self._scan('"to"')
                    return 'op_greater_equal'
                else:# == '"to:"'
                    self._scan('"to:"')
                    return 'op_greater_equal_col'
        elif _token_ == '"than:"':
            self._scan('"than:"')
            return 'op_greater_than_col'
        else:# == '"or"'
            self._scan('"or"')
            _token_ = self._peek('"equal"', '"equal:"')
            if _token_ == '"equal"':
                self._scan('"equal"')
                return 'op_greater_equal'
            else:# == '"equal:"'
                self._scan('"equal:"')
                return 'op_greater_equal_col'

    def ne(self):
        _token_ = self._peek('"notequalto"', '"notequal"', '"doesnotequal"', '"ne"', '"!="', '"!=="', '"#"', '"<>"')
        if _token_ == '"notequalto"':
            self._scan('"notequalto"')
            return 'op_not_equal'
        elif _token_ == '"notequal"':
            self._scan('"notequal"')
            return 'op_not_equal'
        elif _token_ == '"doesnotequal"':
            self._scan('"doesnotequal"')
            return 'op_not_equal'
        elif _token_ == '"ne"':
            self._scan('"ne"')
            return 'op_not_equal'
        elif _token_ == '"!="':
            self._scan('"!="')
            return 'op_not_equal'
        elif _token_ == '"!=="':
            self._scan('"!=="')
            return 'op_not_equal'
        elif _token_ == '"#"':
            self._scan('"#"')
            return 'op_not_equal'
        else:# == '"<>"'
            self._scan('"<>"')
            return 'op_not_equal'

    def ne_col(self):
        _token_ = self._peek('"notequalto:"', '"notequal:"', '"doesnotequal:"', '"ne:"', '"!=:"', '"!==:"', '"#:"', '"<>:"', '"notstartingwith"', '"notstartswith"')
        if _token_ == '"notequalto:"':
            self._scan('"notequalto:"')
            return 'op_not_equal_col'
        elif _token_ == '"notequal:"':
            self._scan('"notequal:"')
            return 'op_not_equal_col'
        elif _token_ == '"doesnotequal:"':
            self._scan('"doesnotequal:"')
            return 'op_not_equal_col'
        elif _token_ == '"ne:"':
            self._scan('"ne:"')
            return 'op_not_equal_col'
        elif _token_ == '"!=:"':
            self._scan('"!=:"')
            return 'op_not_equal_col'
        elif _token_ == '"!==:"':
            self._scan('"!==:"')
            return 'op_not_equal_col'
        elif _token_ == '"#:"':
            self._scan('"#:"')
            return 'op_not_equal_col'
        elif _token_ == '"<>:"':
            self._scan('"<>:"')
            return 'op_not_equal_col'
        elif _token_ == '"notstartingwith"':
            self._scan('"notstartingwith"')
            return 'op_not_equal_col'
        else:# == '"notstartswith"'
            self._scan('"notstartswith"')
            return 'op_not_equal_col'

    def ne_clause(self):
        self._scan('"not"')
        _token_ = self._peek('"equal"', '"equal:"', '"starting"', '"startswith"', '"starts"')
        if _token_ == '"equal"':
            self._scan('"equal"')
            _token_ = self._peek('"to"', '"to:"', 'INT', 'FLOAT', 'STR', '"\\\\[\\\\["', '"\\\\("', '"date"', '"reldate"')
            if _token_ not in ['"to"', '"to:"']:
                return 'op_not_equal'
            elif _token_ == '"to"':
                self._scan('"to"')
                return 'op_not_equal'
            else:# == '"to:"'
                self._scan('"to:"')
                return 'op_not_equal_col'
        elif _token_ == '"equal:"':
            self._scan('"equal:"')
            return 'op_not_equal_col'
        elif _token_ == '"starting"':
            self._scan('"starting"')
            self._scan('"with"')
            return 'op_not_equal_col'
        elif _token_ == '"startswith"':
            self._scan('"startswith"')
            return 'op_not_equal_col'
        else:# == '"starts"'
            self._scan('"starts"')
            self._scan('"with"')
            return 'op_not_equal_col'

    def does_not_clause(self):
        self._scan('"does"')
        self._scan('"not"')
        _token_ = self._peek('"equal"', '"equal:"')
        if _token_ == '"equal"':
            self._scan('"equal"')
            return 'op_not_equal'
        else:# == '"equal:"'
            self._scan('"equal:"')
            return 'op_not_equal_col'

    def eq(self):
        _token_ = self._peek('"equal"', '"equals"', '"equalto"', '"eq"', '"="', '"=="')
        if _token_ == '"equal"':
            self._scan('"equal"')
            self._scan('"to"')
            return 'op_equal'
        elif _token_ == '"equals"':
            self._scan('"equals"')
            return 'op_equal'
        elif _token_ == '"equalto"':
            self._scan('"equalto"')
            return 'op_equal'
        elif _token_ == '"eq"':
            self._scan('"eq"')
            return 'op_equal'
        elif _token_ == '"="':
            self._scan('"="')
            return 'op_equal'
        else:# == '"=="'
            self._scan('"=="')
            return 'op_equal'

    def in_op(self):
        self._scan('"in"')
        return 'op_in'

    def in_col(self):
        self._scan('"in:"')
        return 'op_in_col'

    def not_in(self):
        self._scan('"notin"')
        return 'op_not_in'

    def not_in_col(self):
        self._scan('"notin:"')
        return 'op_not_in_col'

    def between(self):
        self._scan('"between"')
        return 'op_between'

    def contains(self):
        self._scan('"contains"')
        return 'op_contains'

    def op(self):
        _token_ = self._peek('"starting"', '"=:"', '"==:"', '"startingwith"', '"startswith"', '"eq:"', '"lessthan"', '"lt"', '"<"', '"lessthan:"', '"lt:"', '"<:"', '"less"', '"greaterthan"', '"gt"', '">"', '"greaterthan:"', '"gt:"', '">:"', '"greater"', '"greaterthanorequalto"', '"greaterequal"', '"ge"', '">="', '"=>"', '"greaterthanorequalto:"', '"greaterequal:"', '"ge:"', '">=:"', '"=>:"', '"lessthanorequalto"', '"lessequal"', '"le"', '"<="', '"=<"', '"lessthanorequalto:"', '"lessequal:"', '"le:"', '"<=:"', '"=<:"', '"notequalto"', '"notequal"', '"doesnotequal"', '"ne"', '"!="', '"!=="', '"#"', '"<>"', '"notequalto:"', '"notequal:"', '"doesnotequal:"', '"ne:"', '"!=:"', '"!==:"', '"#:"', '"<>:"', '"notstartingwith"', '"notstartswith"', '"not"', '"does"', '"equal"', '"equals"', '"equalto"', '"eq"', '"="', '"=="', '"in"', '"in:"', '"notin"', '"notin:"', '"between"', '"contains"')
        if _token_ in ['"starting"', '"=:"', '"==:"', '"startingwith"', '"startswith"', '"eq:"']:
            starts_with = self.starts_with()
            return starts_with
        elif _token_ in ['"lessthan"', '"lt"', '"<"']:
            lt = self.lt()
            return lt
        elif _token_ in ['"lessthan:"', '"lt:"', '"<:"']:
            lt_col = self.lt_col()
            return lt_col
        elif _token_ == '"less"':
            lt_clause = self.lt_clause()
            return lt_clause
        elif _token_ in ['"greaterthan"', '"gt"', '">"']:
            gt = self.gt()
            return gt
        elif _token_ in ['"greaterthan:"', '"gt:"', '">:"']:
            gt_col = self.gt_col()
            return gt_col
        elif _token_ == '"greater"':
            gt_clause = self.gt_clause()
            return gt_clause
        elif _token_ in ['"greaterthanorequalto"', '"greaterequal"', '"ge"', '">="', '"=>"']:
            ge = self.ge()
            return ge
        elif _token_ in ['"greaterthanorequalto:"', '"greaterequal:"', '"ge:"', '">=:"', '"=>:"']:
            ge_col = self.ge_col()
            return ge_col
        elif _token_ in ['"lessthanorequalto"', '"lessequal"', '"le"', '"<="', '"=<"']:
            le = self.le()
            return le
        elif _token_ in ['"lessthanorequalto:"', '"lessequal:"', '"le:"', '"<=:"', '"=<:"']:
            le_col = self.le_col()
            return le_col
        elif _token_ in ['"notequalto"', '"notequal"', '"doesnotequal"', '"ne"', '"!="', '"!=="', '"#"', '"<>"']:
            ne = self.ne()
            return ne
        elif _token_ not in ['"not"', '"does"', '"equal"', '"equals"', '"equalto"', '"eq"', '"="', '"=="', '"in"', '"in:"', '"notin"', '"notin:"', '"between"', '"contains"']:
            ne_col = self.ne_col()
            return ne_col
        elif _token_ == '"not"':
            ne_clause = self.ne_clause()
            return ne_clause
        elif _token_ == '"does"':
            does_not_clause = self.does_not_clause()
            return does_not_clause
        elif _token_ not in ['"in"', '"in:"', '"notin"', '"notin:"', '"between"', '"contains"']:
            eq = self.eq()
            return eq
        elif _token_ == '"in"':
            in_op = self.in_op()
            return in_op
        elif _token_ == '"in:"':
            in_col = self.in_col()
            return in_col
        elif _token_ == '"notin"':
            not_in = self.not_in()
            return not_in
        elif _token_ == '"notin:"':
            not_in_col = self.not_in_col()
            return not_in_col
        elif _token_ == '"between"':
            between = self.between()
            return between
        else:# == '"contains"'
            contains = self.contains()
            return contains

    def goal(self):
        expr = self.expr()
        END = self._scan('END')
        return expr

    def sgoal(self):
        sexpr = self.sexpr()
        END = self._scan('END')
        return sexpr

    def expr(self):
        factor = self.factor()
        f = factor
        while self._peek('"or"', 'END', '"\\\\)"') == '"or"':
            self._scan('"or"')
            factor = self.factor()
            f = soomfunc.union(f, factor)
        return f

    def factor(self):
        comparison = self.comparison()
        f = comparison
        while self._peek('"and"', '"or"', 'END', '"\\\\)"') == '"and"':
            self._scan('"and"')
            comparison = self.comparison()
            f = soomfunc.intersect(f, comparison)
        return f

    def comparison(self):
        _token_ = self._peek('"\\\\("', '"not"', 'ID')
        if _token_ == 'ID':
            col = self.col()
            op = self.op()
            term = self.term()
            return col.filter_op(op, term, self.filter_keys)
        elif _token_ == '"\\\\("':
            self._scan('"\\\\("')
            expr = self.expr()
            self._scan('"\\\\)"')
            return expr
        else:# == '"not"'
            self._scan('"not"')
            comparison = self.comparison()
            return soomfunc.outersect(Numeric.arrayrange(len(self.dataset)), comparison)

    def term(self):
        _token_ = self._peek('INT', 'FLOAT', 'STR', '"\\\\[\\\\["', '"\\\\("', '"date"', '"reldate"')
        if _token_ == 'INT':
            INT = self._scan('INT')
            return int(INT)
        elif _token_ == 'FLOAT':
            FLOAT = self._scan('FLOAT')
            return float(FLOAT)
        elif _token_ == 'STR':
            STR = self._scan('STR')
            return dequote(STR)
        elif _token_ == '"\\\\[\\\\["':
            self._scan('"\\\\[\\\\["')
            sexpr = self.sexpr()
            self._scan('"\\\\]\\\\]"')
            return sexpr
        elif _token_ == '"\\\\("':
            self._scan('"\\\\("')
            while 1:
                term = self.term()
                term_list = [term]
                while self._peek('","', '"\\\\)"', 'INT', 'FLOAT', 'STR', '"\\\\[\\\\["', '"\\\\("', '"date"', '"reldate"') == '","':
                    self._scan('","')
                    term = self.term()
                    term_list.append(term)
                if self._peek('INT', 'FLOAT', 'STR', '"\\\\[\\\\["', '"\\\\("', '"date"', '"reldate"', '","', '"\\\\)"') not in ['INT', 'FLOAT', 'STR', '"\\\\[\\\\["', '"\\\\("', '"date"', '"reldate"']: break
            self._scan('"\\\\)"')
            return term_list
        elif _token_ == '"date"':
            self._scan('"date"')
            _token_ = self._peek('"\\\\("', 'DATE')
            if _token_ == '"\\\\("':
                self._scan('"\\\\("')
                INT = self._scan('INT')
                year = int(INT)
                self._scan('","')
                INT = self._scan('INT')
                month = int(INT)
                self._scan('","')
                INT = self._scan('INT')
                day = int(INT)
                self._scan('"\\\\)"')
                return mx.DateTime.Date(year, month, day)
            else:# == 'DATE'
                DATE = self._scan('DATE')
                return mx.DateTime.ISO.ParseDate(DATE)
        else:# == '"reldate"'
            self._scan('"reldate"')
            kwargs = self.kwargs()
            return relativeDate(**kwargs)

    def col(self):
        ID = self._scan('ID')
        return self.dataset.get_column(ID)

    def kwargs(self):
        self._scan('"\\\\("')
        kwargs = {}
        _token_ = self._peek('ID', '","', '"\\\\)"')
        if _token_ != 'ID':
            pass
        else:# == 'ID'
            ID = self._scan('ID')
            self._scan('"="')
            term = self.term()
            kwargs[ID] = term
            while self._peek('","', '"\\\\)"') == '","':
                self._scan('","')
                ID = self._scan('ID')
                self._scan('"="')
                term = self.term()
                kwargs[ID] = term
        self._scan('"\\\\)"')
        return kwargs

    def sexpr(self):
        sfactor = self.sfactor()
        f = Search.Disjunction(sfactor)
        while self._peek('"\\\\|"', 'END', '"\\\\]\\\\]"', '"\\\\)"') == '"\\\\|"':
            self._scan('"\\\\|"')
            sfactor = self.sfactor()
            f.append(sfactor)
        return f

    def sfactor(self):
        sphrase = self.sphrase()
        f = sphrase
        while self._peek('"-"', '"&"', '"<"', '">"', '"~"', '"\\""', 'WORD', '"\\\\("', '"\\\\|"', 'END', '"\\\\]\\\\]"', '"\\\\)"') not in ['"\\\\|"', 'END', '"\\\\]\\\\]"', '"\\\\)"']:
            _token_ = self._peek('"-"', '"&"', '"<"', '">"', '"~"', '"\\""', 'WORD', '"\\\\("')
            if _token_ == '"&"':
                sconjop = self.sconjop()
                sphrase = self.sphrase()
                f = Search.Conjunction(sconjop, f, sphrase)
            elif _token_ not in ['"-"', '"\\""', 'WORD', '"\\\\("']:
                snearop = self.snearop()
                op = snearop; nearness = Search.Conjunction.DEFAULT_NEARNESS
                _token_ = self._peek('"\\\\["', '"\\""', 'WORD', '"\\\\("')
                if _token_ == '"\\\\["':
                    self._scan('"\\\\["')
                    INT = self._scan('INT')
                    self._scan('"\\\\]"')
                    nearness = int(INT)
                else:# in ['"\\""', 'WORD', '"\\\\("']
                    pass
                sphrase = self.sphrase()
                f = Search.Conjunction(op, f, sphrase, nearness)
            else:# in ['"-"', '"\\""', 'WORD', '"\\\\("']
                op = '&'
                _token_ = self._peek('"-"', '"\\""', 'WORD', '"\\\\("')
                if _token_ == '"-"':
                    self._scan('"-"')
                    op = '&!'
                else:# in ['"\\""', 'WORD', '"\\\\("']
                    pass
                sphrase = self.sphrase()
                f = Search.Conjunction(op, f, sphrase)
        return f

    def sconjop(self):
        self._scan('"&"')
        op = '&'
        _token_ = self._peek('"-"', '"\\""', 'WORD', '"\\\\("')
        if _token_ == '"-"':
            self._scan('"-"')
            op = '&!'
        else:# in ['"\\""', 'WORD', '"\\\\("']
            pass
        return op

    def snearop(self):
        _token_ = self._peek('"<"', '">"', '"~"')
        if _token_ == '"<"':
            self._scan('"<"')
            return '<'
        elif _token_ == '">"':
            self._scan('">"')
            return '>'
        else:# == '"~"'
            self._scan('"~"')
            return '~'

    def sphrase(self):
        _token_ = self._peek('"\\""', 'WORD', '"\\\\("')
        if _token_ != '"\\""':
            sterm = self.sterm()
            return sterm
        else:# == '"\\""'
            self._scan('"\\""')
            words = []
            while 1:
                sterm = self.sterm()
                words.append(sterm)
                if self._peek('WORD', '"\\\\("', '"\\""') not in ['WORD', '"\\\\("']: break
            self._scan('"\\""')
            return Search.Phrase(words)

    def sterm(self):
        _token_ = self._peek('WORD', '"\\\\("')
        if _token_ == 'WORD':
            WORD = self._scan('WORD')
            return Search.Word(WORD)
        else:# == '"\\\\("'
            self._scan('"\\\\("')
            sexpr = self.sexpr()
            self._scan('"\\\\)"')
            return sexpr


def parse(rule, text):
    P = soomparse(soomparseScanner(text))
    return wrap_error_reporter(P, rule)




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
