#!/usr/bin/python
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
#
# $Id: nea.py 2626 2007-03-09 04:35:54Z andrewm $
# $Source: /usr/local/cvsroot/NSWDoH/SOOMv0/web/nea.py,v $

# Standard libraries
import sys, os
import copy

# Albatross, http://www.object-craft.com.au/projects/albatross/
from albatross import SimpleApp, SimpleAppContext

def is_fcgi():
    # If there's a better way of detecting a FastCGI environment, I'd love to
    # hear it.
    import socket, errno
    try:
        s=socket.fromfd(sys.stdin.fileno(), socket.AF_INET,
                        socket.SOCK_STREAM)
    except socket.error:
        return False
    try:
        try:
            s.getpeername()
        except socket.error, (eno, errmsg):
            return eno == errno.ENOTCONN
    finally:
        s.close()

use_fcgi = is_fcgi()
if use_fcgi:
    from albatross.fcgiapp import Request, running
else:
    from albatross.cgiapp import Request

# SOOM, NSWDoH
import SOOMv0 

# Application modules
from libsoomexplorer.workspace import Workspace
from libsoomexplorer.filter import ExpressionEdit, Filter, FilterError
from libsoomexplorer.undo import UndoError
from libsoomexplorer.common import *

import config

app_dir = os.path.dirname(__file__)
page_dir = os.path.join(app_dir, 'pages')
sys.path.insert(0, app_dir)


class PageBase:
    def page_display(self, ctx):
        ctx.locals.title = ctx.locals.appname
        ctx.run_template(self.name + '.html')

    def dispatch(self, ctx, *objects):
        for field in ctx.request.field_names():
            if field.endswith('.x'):
                field = field[:-2]
            elif field.endswith('.y'):
                continue
            subfields = field.split('/')
            for o in objects:
                meth = getattr(o, 'do_' + subfields[0], None)
                if meth:
                    meth(ctx, *subfields[1:])


class StartPage(PageBase):
    name = 'start'

    def page_enter(self, ctx):
        ctx.locals.workspace = Workspace()
        ctx.add_session_vars('workspace')

    def page_display(self, ctx):
        ctx.locals.soomversion = SOOMv0.version
        PageBase.page_display(self, ctx)

    def page_process(self, ctx):
        workspace = ctx.locals.workspace
        workspace.errorstr = ''
        try:
            if workspace.dsname:
                workspace.set_dsname()
                workspace.set_plottype()
                if ctx.req_equals('ok'):
                    ctx.push_page('params')
                elif ctx.req_equals('explore'):
                    ctx.push_page('explore')
        except SOOMv0.Error, e:
            workspace.errorstr = str(e)


class ParamPage(PageBase):
    name = 'params'

    def page_display(self, ctx):
        workspace = ctx.locals.workspace
        label = workspace.dslabel or workspace.dsname
        ctx.locals.title = 'Dataset %r - %s' % (label, ctx.locals.appname)
        ctx.locals.condcolparams = workspace.get_condcolparams()
        PageBase.page_display(self, ctx)

    def page_process(self, ctx):
        workspace = ctx.locals.workspace
        workspace.refresh()
        workspace.errorstr = ''
        if ctx.req_equals('back'):
            ctx.pop_page()
        try:
            workspace.set_plottype()
            if ctx.req_equals('ok'):
                if workspace.go() and workspace.output.inline:
                    ctx.push_page('result')
            elif ctx.req_equals('plottype_reset'):
                workspace.clear_params()
            elif ctx.req_equals('hide_params'):
                workspace.plottype.hide_params = True
                if workspace.output.have_files() and workspace.output.inline:
                    ctx.push_page('result')
            elif ctx.req_equals('edit_condcolparams'):
                if not len(workspace.get_condcolparams()):
                    raise UIError('No conditioning columns?')
                ctx.push_page('condcolparams')
            elif ctx.req_equals('edit_exposed'):
                ctx.push_page('twobytwoparams', 
                              workspace.params.exposure_params)
            elif ctx.req_equals('edit_outcome'):
                ctx.push_page('twobytwoparams', 
                              workspace.params.outcome_params)
            else:
                self.dispatch(ctx, workspace.params)
        except SOOMv0.Error, e:
            workspace.errorstr = str(e)


class ResultPage(PageBase):
    name = 'result'

    def page_process(self, ctx):
        workspace = ctx.locals.workspace
        if ctx.req_equals('back'):
            ctx.pop_page('start')
        elif ctx.req_equals('show_params'):
            workspace.plottype.hide_params = False
            ctx.pop_page()


class FilterPage(PageBase):
    name = 'filter'
    colnamefields = 'dtcol', 'disccol', 'textcol', 'othercol'

    def page_enter(self, ctx, dsparams):
        ctx.locals.dsparams = dsparams
        ctx.add_session_vars('dsparams')
        ctx.locals.errorstr = ''
        filter = ctx.locals.dsparams.edit_filter
        if not filter.name:
            filter.start_edit_node(filter.root.path)
        ctx.locals.filter = filter
        ctx.add_session_vars('filter')
        for a in self.colnamefields:
            setattr(ctx.locals, a, '')
        ctx.add_session_vars(*self.colnamefields)
        ctx.locals.colvalselect = None
        ctx.add_session_vars('colvalselect')
        ctx.locals.delete_confirm = False
        ctx.add_session_vars('delete_confirm')

    def page_leave(self, ctx):
        ctx.locals.dsparams.edit_filter = None
        ctx.del_session_vars('dsparams')
        ctx.del_session_vars('filter')
        ctx.del_session_vars(*self.colnamefields)
        ctx.del_session_vars('colvalselect')
        ctx.del_session_vars('delete_confirm')

    def page_display(self, ctx):
        filter = ctx.locals.filter
        workspace = ctx.locals.workspace
        if filter.edit_expr and hasattr(filter.edit_expr, 'colname'):
            ctx.locals.colvalselect = filter.edit_expr.value
            ctx.locals.search_result = ctx.locals.colvalselect.search(workspace)
            for a in self.colnamefields:
                setattr(ctx.locals, a, filter.edit_expr.colname)
        else:
            ctx.locals.colvalselect = None
            ctx.locals.search_result = []
        PageBase.page_display(self, ctx)

    def page_process(self, ctx):
        filter = ctx.locals.filter
        workspace = ctx.locals.workspace
        ctx.locals.errorstr = ''
        try:
            for field in ctx.request.field_names():
                if field.endswith('.x'):
                    field = field[:-2]
                elif field.endswith('.y'):
                    continue
                args = field.split('/')
                op, args = args[0], args[1:]
                if op == 'node':
                    return filter.start_edit_node(*args)
                elif op == 'sop':
                    return ctx.locals.colvalselect.sop(workspace, *args)
            if ctx.req_equals('cancel'):
                ctx.pop_page()
            elif ctx.req_equals('delete'):
                ctx.locals.delete_confirm = True
            elif ctx.req_equals('delete_okay'):
                try:
                    ctx.locals.dsparams.delete_filter(filter)
                finally:
                    ctx.locals.delete_confirm = False
                ctx.pop_page()
            elif ctx.req_equals('delete_back'):
                ctx.locals.delete_confirm = False
            elif ctx.req_equals('save'):
                ctx.locals.dsparams.save_filter(filter)
                ctx.pop_page()
            elif ctx.req_equals('okay'):
                ctx.locals.dsparams.use_filter(filter)
                ctx.pop_page()
            elif ctx.req_equals('undo'):
                ctx.locals.filter.undo()
            elif ctx.req_equals('redo'):
                ctx.locals.filter.redo()
            elif ctx.req_equals('do_edit_info'):
                filter.start_edit_info()
            elif ctx.req_equals('edit_node_close'):
                filter.end_edit_node()
            elif filter.edit_info:
                if ctx.req_equals('info_edit_apply'):
                    filter.apply_info()
                elif ctx.req_equals('info_edit_close'):
                    filter.end_edit_info()
            elif filter.edit_expr:
                if ctx.req_equals('back'):
                    filter.expr_back()
                elif ctx.req_equals('delete_node'):
                    filter.del_expr(filter.edit_expr.node)
                elif ctx.req_equals('add_and'):
                    filter.add_andor(filter.edit_expr.node, 'and')
                elif ctx.req_equals('add_or'):
                    filter.add_andor(filter.edit_expr.node, 'or')
                elif filter.edit_expr.state == filter.edit_expr.EDITCOL:
                    for field in self.colnamefields:
                        colname = getattr(ctx.locals, field, None)
                        if colname:
                            filter.edit_expr.colname = colname
                            filter.expr_forward(workspace)
                            break
                elif ctx.req_equals('ok'):
                    filter.expr_forward(workspace)
            elif filter.edit_andor:
                if ctx.req_equals('add_and'):
                    filter.add_andor(filter.edit_andor.node, 'and')
                elif ctx.req_equals('add_or'):
                    filter.add_andor(filter.edit_andor.node, 'or')
                elif ctx.req_equals('add_expr'):
                    filter.add_expr(filter.edit_andor.node)
                else:
                    filter.apply_andor()
        except (UndoError, FilterError), e:
            ctx.locals.errorstr = str(e)


class ExplorePage(PageBase):
    name = 'explore'

    def page_enter(self, ctx):
        ctx.locals.show_col = None
        ctx.add_session_vars('show_col')

    def page_display(self, ctx):
        ctx.locals.ds = ctx.locals.workspace.get_dataset()
        PageBase.page_display(self, ctx)

    def page_process(self, ctx):
        if ctx.req_equals('back'):
            ctx.pop_page()
        elif ctx.req_equals('allcols'):
            ctx.locals.show_col = None
        else:
            for field in ctx.request.field_names():
                if field.startswith('view_'):
                    ctx.locals.show_col = field[len('view_'):]

    def page_leave(self, ctx):
        ctx.del_session_vars('show_col')


class CondColParamsPage(PageBase):
    name = 'condcolparams'

    def page_enter(self, ctx):
        workspace = ctx.locals.workspace
        ctx.locals.condcolparams = workspace.get_condcolparams()
        ctx.locals.colvalselect = None
        ctx.add_session_vars('condcolparams', 'colvalselect')

    def page_leave(self, ctx):
        ctx.del_session_vars('condcolparams', 'colvalselect')

    def page_display(self, ctx):
        condcolparams = ctx.locals.condcolparams
        workspace = ctx.locals.workspace
        # We want the search result to be transient
        ctx.locals.search_result = condcolparams.maybe_search(workspace)
        PageBase.page_display(self, ctx)

    def page_process(self, ctx):
        workspace = ctx.locals.workspace
        condcolparams = ctx.locals.condcolparams
        colvalselect = ctx.locals.colvalselect
        if ctx.req_equals('okay'):
            ctx.pop_page()
            param_map = condcolparams.get_map(workspace)
            workspace.params.condcolparams.update(param_map)
        elif ctx.req_equals('back'):
            ctx.pop_page()
        elif ctx.req_equals('clear'):
            condcolparams.clear(workspace)
        elif ctx.req_equals('edit_okay'):
            condcolparams.done_edit(workspace)
            ctx.locals.colvalselect = None
        else:
            for field in ctx.request.field_names():
                if field.endswith('.x'):
                    field = field[:-2]
                elif field.endswith('.y'):
                    continue
                subfields = field.split('/')
                if subfields[0] == 'col':
                    condcolparams.do_col(workspace, *subfields[1:])
                    ctx.locals.colvalselect = condcolparams.edit_col.edit
                elif subfields[0] == 'sop':
                    colvalselect.sop(workspace, *subfields[1:])


class TwoByTwoParamsPage(PageBase):
    name = 'twobytwoparams'

    def page_enter(self, ctx, params):
        params.save_undo()
        ctx.locals.params = params
        ctx.add_session_vars('params')

    def page_leave(self, ctx):
        ctx.del_session_vars('params')

    def page_process(self, ctx):
        workspace = ctx.locals.workspace
        if ctx.req_equals('back'):
            ctx.locals.params.undo()
            ctx.pop_page()
        elif ctx.req_equals('okay'):
            param_map = ctx.locals.params.get_map(workspace)
            workspace.params.condcolparams.update(param_map)
            ctx.locals.params.clear_undo()
            ctx.pop_page()
        else:
            self.dispatch(ctx, ctx.locals.params)
        ctx.locals.params.search(workspace)


class Context(SimpleAppContext):
    def __init__(self, app):
        SimpleAppContext.__init__(self, app)
        for attr in ('appname', 'apptitle'):
            setattr(self.locals, attr, getattr(config, attr))
            self.add_session_vars(attr)
        self.run_template_once('macros.html')

class Application(SimpleApp):
    pages = (
        StartPage, ParamPage, ResultPage, FilterPage, ExplorePage,
        CondColParamsPage, TwoByTwoParamsPage,
    )

    def __init__(self):
        SimpleApp.__init__(self,
                           base_url = 'nea.py',
                        #  module_path=page_dir,
                           template_path=page_dir,
                           start_page='start',
                           secret=config.session_secret)
        for page in self.pages:
            self.register_page(page.name, page())

    def create_context(self):
        return Context(self)


SOOMv0.soom.setpath(config.soompath, config.data_dir)
app = Application()

if __name__=="__main__":
    if not os.path.isabs(config.soompath):
        config.soompath = os.path.join(app_dir, config.soompath)

    if use_fcgi:
        while running():
            app.run(Request())
    else:
        app.run(Request())
