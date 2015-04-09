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
# $Id: filter.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/libsoomexplorer/filter.py,v $

# Standard libraries
import time
import re

# eGenix mx.Tools, http://www.egenix.com/files/python/mxTools.html
import mx

# SOOM NSWDoH
import SOOMv0

# Application modules
from libsoomexplorer import colvals
from libsoomexplorer.undo import UndoMixin

class Node:
    def __init__(self):
        self.children = []

    def update_path(self, path='0'):
        self.path = path
        for i, child in enumerate(self.children):
            child.update_path('%s_%d' % (path, i))

    def height(self):
        return sum([child.height() for child in self.children]) or 1

    def find_node(self, path):
        """ Given a PATH, find a node """
        if path == self.path:
            return self
        for child in self.children:
            node = child.find_node(path)
            if node:
                return node

    def find_parent_node(self, child_node):
        """ Given a node, find the parent """
        if child_node in self.children:
            return self
        for child in self.children:
            node = child.find_parent_node(child_node)
            if node:
                return node

class ContainerNode(Node):
    def __init__(self, name, *children):
        Node.__init__(self)
        self.name = name
        self.children = list(children)

    def describe(self, dsname):
        return self.name

    def as_string(self):
        children_as_str = [child.as_string() 
                           for child in self.children
                           if child.is_complete()]
        if not children_as_str:
            return ''
        return '(%s)' % ((' %s ' % self.name).join(children_as_str))

    def is_complete(self):
        for child in self.children:
            if child.is_complete():
                return True
        return False

class LeafNode(Node):
    def __init__(self, colname, op, value):
        Node.__init__(self)
        self.colname = colname
        self.op = op
        self.value = value

    def describe(self, dsname):
        def fmt(v):
            return col.do_format(col.do_outtrans(v))

        if not self.colname:
            return '???'
        col = SOOMv0.dsload(dsname).get_column(self.colname)
        if type(self.value) is tuple:
            value = ', '.join([fmt(v) for v in self.value])
        else:
            value = fmt(self.value)
        if self.op == 'contains':
            value = "[[%s]]" % value
        return '%s %s %s' % (col.label, self.op, value)

    def as_string(self):
        if not self.is_complete():
            return ''
        value = self.value
        if type(value) is mx.DateTime.DateTimeType:
            value = 'date(%s,%s,%s)' % (value.year, value.month, value.day)
        elif type(value) is tuple:
            # So 1-tuple is correctly represented (no trailing comma)
            value = '(%s)' % (', '.join([repr(v) for v in value]))
        elif self.op == "contains":
            value = "[[%s]]" % value
        else:
            value = repr(value)
        return '%s %s %s' % (self.colname, self.op, value)

    def is_complete(self):
        return self.colname and self.op

class FilterError(Exception): pass

ops = [
    ('==', 'equal'),
    ('==:', 'starts with'),
    ('!=', 'not equal'),
    ('!=:', 'does not start with'),
    ('<', 'less than'),
    ('<=', 'less than or equal'),
    ('<:', 'less than starting'),
    ('<=:', 'less than or equal starting'),
    ('>', 'greater than'),
    ('>:', 'greater than starting'),
    ('>=', 'greater than or equal'),
    ('>=:', 'greater than or equal starting'),
    ('in', 'in'),
    ('in:', 'prefix in'),
    ('notin', 'not in'),
    ('notin:', 'prefix not in'),
    ('contains', 'contains'),
]

class ExprValueBase:
    markup = 'none'

    def __init__(self, name, value, multiple = False):
        pass

    def search(self, workspace):
        pass

    def as_pytypes(self, workspace):
        return None

    def pretty_value(self, workspace):
        return ''

    def __nonzero__(self):
        return False

    def show_search_box(self, workspace):
        return False

class ExprValueNull(ExprValueBase):
    pass

class ExprValue(ExprValueBase):
    markup = 'general'
    split_re = re.compile('[ ]*,[ ]*')

    def __init__(self, name, value, multiple = False):
        self.name = name
        self.value = value
        self.multiple = multiple

    def search(self, workspace):
        pass

    def as_pytypes(self, workspace):
        col = workspace.get_dataset()[self.name]
        if self.multiple:
            value = self.value
            if type(self.value) in (str, unicode):
                value = self.split_re.split(self.value.strip())
            elif self.value is None:
                value = []
            return tuple([colvals.to_datatype(col, v) for v in value])
        else:
            return colvals.to_datatype(col, self.value)

    def strval(self):
        if self.value is None:
            return ''
        if self.multiple:
            return ', '.join(self.value)
        else:
            return str(self.value)

    def pretty_value(self, workspace):
        col = workspace.get_dataset()[self.name]
        value = self.as_pytypes(workspace)
        if self.multiple:
            return ', '.join([colvals.shorten_trans(col, v) for v in value])
        else:
            return colvals.shorten_trans(col, value)

    def __repr__(self):
        return '%s(%r, %r, %r)' %\
            (self.__class__.__name__,
             self.name,
             self.value,
             self.multiple)

class ExprValueDiscrete(colvals.ColValSelect, ExprValueBase):
    markup = 'discrete'

    def show_search_box(self, workspace):
        return self.cardinality_is_high(workspace)

class ExprValueDate(ExprValueBase):
    markup = 'date'

    def __init__(self, name, value, multiple = False):
        if not value:
            value = mx.DateTime.now()
        self.year = value.year
        self.month = value.month
        self.day = value.day

    def search(self, workspace):
        pass

    def as_pytypes(self, workspace):
        try:
            return mx.DateTime.DateTime(int(self.year), 
                                        int(self.month), 
                                        int(self.day))
        except mx.DateTime.Error, e:
            raise FilterError('date: %s' % e)

    def pretty_value(self, workspace):
        return '%s-%s-%s' % (self.year, self.month, self.day)

    def yearopt(self):
        return range(2050, 1900, -1)

    def monthopt(self):
        months = [(i, n) for i, n in mx.DateTime.Month.items()
                         if type(i) is int]
        months.sort()
        return months

    def dayopt(self):
        return range(1, 32)

class ExpressionEdit:
    EDITCOL = 0
    EDITOP = 1
    EDITVALUE = 2

    def __init__(self, dsname, node):
        self.dsname = dsname
        self.ops = ops
        self.state = self.EDITCOL
        self.colname = node.colname
        self.op = node.op
        self.node = node
        self.__value_type = None
        self.set_value(node.value)

    def get_column(self):
        if self.colname:
            ds = SOOMv0.dsload(self.dsname)
            return ds.get_column(self.colname)

    def is_set_op(self):
        return self.op in ('in', 'in:', 'notin', 'notin:')

    def is_prefix_op(self):
        return self.op.endswith(':')

    def set_value(self, value = None):
        col = self.get_column()
        if not self.colname or not self.op:
            value_method = ExprValueNull
        elif col.is_datetimetype():
            value_method = ExprValueDate
        elif not col.is_discrete() or self.is_prefix_op():
            value_method = ExprValue
        else:
            value_method = ExprValueDiscrete
        value_type = self.colname, value_method, self.is_set_op()
        if value_type != self.__value_type:
            self.value = value_method(self.colname, value, 
                                      multiple=self.is_set_op())
            self.__value_type = value_type

    def colname_select(self, filter = None):
        if filter is None:
            filter = True
        elif filter == 'datetime':
            filter = lambda c: c.is_datetimetype()
        elif filter == 'discrete':
            filter = lambda c: c.is_discrete() and not c.is_datetimetype() \
                    and not c.is_searchabletext()
        elif filter == 'text':
            filter = lambda c: c.is_searchabletext()
        elif filter == 'other':
            filter = lambda c: not c.is_discrete() and not c.is_datetimetype() \
                    and not c.is_searchabletext()
        else:
            raise ValueError('bad column filter value')
        ds = SOOMv0.dsload(self.dsname)
        cols = [(col.label, col.name)
                for col in ds.get_columns()
                if filter(col)]
        cols.sort()
        cols.insert(0, ('-- select --', ''))
        return [(name, label) for label, name in cols]

    def get_available_values(self):
        """
        For discrete columns, return a list of potential values
        """
        col = self.get_column()
        if not col.is_discrete():
            return
        values = [(v, str(col.do_outtrans(v))[:45]) 
                  for v in col.inverted.keys()]
        if col.is_ordered():
            values.sort()
        else:
            values = [(l, v) for v, l in values]
            values.sort()
            values = [(v, l) for l, v in values]
        return values

    def pretty_value(self, workspace):
        return self.value.pretty_value(workspace)

    def back(self):
        self.state -= 1

    def forward(self):
        self.state += 1
        self.set_value()

    def show_search_box(self, workspace):
        return (self.state == self.EDITVALUE 
                and self.value.show_search_box(workspace))

class FilterInfo:
    def __init__(self, filter):
        self.name = filter.name
        self.label = filter.label

class AndOrEdit:
    def __init__(self, dsname, node):
        self.dsname = dsname
        self.node = node
        self.name = node.name

class Filter(UndoMixin):
    def __init__(self, dsname):
        UndoMixin.__init__(self)
        assert dsname
        self.dsname = dsname
        self.name = None
        self.label = None
        self.root = LeafNode(None, None, None)
        self.root.update_path()
        self.clear_edit()
        self.updatetime = time.time()

    def clear_edit(self):
        self.edit_expr = None
        self.edit_info = None
        self.edit_andor = None

    def node_is_selected(self, node):
        return ((self.edit_expr and self.edit_expr.node == node)
                or (self.edit_andor and self.edit_andor.node == node))

    def undo(self):
        self.clear_edit()
        UndoMixin.undo(self)

    def redo(self):
        self.clear_edit()
        UndoMixin.redo(self)

    def start_edit_node(self, path):
        self.clear_edit()
        node = self.root.find_node(path)
        if not node:
            raise LookupError('node path %s not found' % path)
        if isinstance(node, ContainerNode):
            self.edit_andor = AndOrEdit(self.dsname, node)
        else:
            self.edit_expr = ExpressionEdit(self.dsname, node)

    def end_edit_node(self):
        self.edit_expr = None
        self.edit_andor = None

    def add_expr(self, node):
        new_node = LeafNode(None, None, None)
        self._add_expr(node, new_node)

    def _add_expr(self, node, new_node):
        # AM - I'm not convinced it's safe saving node instances in 
        # the undo data.
        self._record_undo('_del_expr', new_node)
        node.children.append(new_node)
        self.root.update_path()
        self.clear_edit()
        self.edit_expr = ExpressionEdit(self.dsname, new_node)

    def del_expr(self, node):
        self._del_expr(node)

    def _del_expr(self, node):
        parent = self.root.find_parent_node(node)
        if not parent:
            return                      # presumably this is the root node!
        if len(parent.children) == 2:
            if parent.children[0] == node:
                other_node = parent.children[1]
            else:
                other_node = parent.children[0]
            self._del_andor(parent, other_node)
        else:
            self._record_undo('_add_expr', parent, node)
            parent.children.remove(node)
            self.root.update_path()
            self.end_edit_node()

    def add_andor(self, node, name):
        # Insert at "node" a new and/or node, moving "node" down, and adding
        # a new leaf node.
        new_node = ContainerNode(name)
        new_node.children.append(node)
        new_expr_node = LeafNode(None, None, None)
        new_node.children.append(new_expr_node)
        self._add_andor(new_node, node)
        self.edit_expr = ExpressionEdit(self.dsname, new_expr_node)

    def _add_andor(self, new_node, child):
        # Insert and/or new_node at "child", moving child down 
        self._record_undo('_del_andor', new_node, child)
        parent = self.root.find_parent_node(child)
        if parent:
            for i, n in enumerate(parent.children):
                if n == child:
                    parent.children[i] = new_node
        else:
            self.root = new_node
        self.root.update_path()
        self.clear_edit()
        if isinstance(child, LeafNode):
            self.edit_expr = ExpressionEdit(self.dsname, child)

    def _del_andor(self, node, child):
        # Delete and/or node, moving "child" up tree
        parent = self.root.find_parent_node(node)
        self._record_undo('_add_andor', node, child)
        if parent:
            for i, n in enumerate(parent.children):
                if n == node:
                    parent.children[i] = child
        else:
            self.root = child
        self.root.update_path()
        self.clear_edit()
        if isinstance(child, LeafNode):
            self.edit_expr = ExpressionEdit(self.dsname, child)

    def expr_back(self):
        if self.edit_expr.state == self.edit_expr.EDITCOL:
            self.end_edit_node()
        else:
            self.edit_expr.back()

    def expr_forward(self, workspace):
        if self.edit_expr.state == self.edit_expr.EDITVALUE:
            self._set_expr(self.edit_expr.node, self.edit_expr.colname,
                           self.edit_expr.op, 
                           self.edit_expr.value.as_pytypes(workspace))
            self.end_edit_node()
        else:
            self.edit_expr.forward()

    def _set_expr(self, node, colname, op, value):
        self._record_undo('_set_expr', node, node.colname, node.op, node.value)
        node.colname = colname
        node.op = op
        node.value = value

    def start_edit_info(self):
# AAA
#        self.clear_edit()
        self.edit_info = FilterInfo(self)

    def end_edit_info(self):
        self.edit_info = None

    def apply_info(self):
        self._set_info(self.edit_info.name, self.edit_info.label)
        self.end_edit_info()
# AAA
#        if not self.root.children:
#            self.start_edit_node(self.root.path)

    def _set_info(self, name, label):
        self._record_undo('_set_info', self.name, self.label)
        self.name = name
        if not label:
            label = self.name
        self.label = label
# AAA
#        if not self.edit_info:
#            self.start_edit_info()

    def apply_andor(self):
        self._set_andor(self.edit_andor.node, self.edit_andor.name)

    def _set_andor(self, node, name):
        self._record_undo('_set_andor', node, node.name)
        node.name = name
        if not self.edit_info:
            self.start_edit_node(node.path)

    def as_string(self):
        return self.root.as_string()

    def in_edit(self):
        return self.edit_expr or self.edit_andor or self.edit_info
