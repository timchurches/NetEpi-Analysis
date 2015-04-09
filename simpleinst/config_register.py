#
#   The contents of this file are subject to the HACOS License Version 1.2
#   (the "License"); you may not use this file except in compliance with
#   the License.  Software distributed under the License is distributed
#   on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or
#   implied. See the LICENSE file for the specific language governing
#   rights and limitations under the License.  The Original Software
#   is "SimpleInst". The Initial Developer of the Original
#   Software is the Health Administration Corporation, incorporated in
#   the State of New South Wales, Australia.  Copyright (C) 2004 Health
#   Administration Corporation. All Rights Reserved.
#

import sys
import os
import imp
import tempfile
from simpleinst.defaults import Defaults
from simpleinst.utils import chown, chmod, normjoin, make_dirs

class ConfigBase:
    def __init__(self, source_name):
        self.config_source = source_name
        self.base_dir = os.path.dirname(sys.modules['__main__'].__file__)
        self.python = os.path.abspath(sys.executable)

class Config:
    def __init__(self):
        self._app_config = ConfigBase('Installer')
        self._cmdline_config = ConfigBase('Command Line')
        self._sources = [self._cmdline_config, self._app_config]
        self._offset = len(self._sources)
        self._sources.append(Defaults())

    def add(self, source):
        self._sources.insert(self._offset, source)

    def add_file(self, name = 'config', path = ''):
        path = normjoin(self.base_dir, path)
        try:
            f, filename, extras = imp.find_module(name, [path])
        except ImportError, e:
            raise ImportError('%s (in %s)' % (e, path))
        config_mod = imp.load_module(name, f, filename, extras)
        setattr(config_mod, 'config_source', filename)
        self.add(config_mod)

    def add_cmdline(self):
        for arg in sys.argv[1:]:
            try:
                a, v = arg.split('=')
            except ValueError:
                sys.exit('Unknown command line option: %r' % arg)
            # Attempt to cast cmdline value to existing type (eg default)
            try:
                t = type(getattr(self, a))
            except AttributeError:
                pass
            else:
                if t is bool:
                    v = v.lower() in ('t', 'true', 'y', 'yes', '1')
                else:
                    try:
                        v = t(v)
                    except (ValueError, TypeError):
                        pass
            setattr(self._cmdline_config, a, v)

    def __getattr__(self, a):
        for source in self._sources:
            try:
                return getattr(source, a)
            except AttributeError:
                pass
        raise AttributeError('attribute "%s" not found' % a)

    def __setattr__(self, a, v):
        if a.startswith('_'):
            self.__dict__[a] = v
        else:
            setattr(self._app_config, a, v)

    def _config_dict(self):
        """
        Produce a dictionary of the current config
        """
        class _ConfigItem(object):
            __slots__ = 'value', 'source'

            def __init__(self, value, source):
                self.value = value
                self.source = source

        config = {}
        for source in self._sources:
            for a in dir(source):
                if not config.has_key(a) and not a.startswith('_') \
                    and a != 'config_source':
                    v = getattr(source, a)
                    if not callable(v):
                        config[a] = _ConfigItem(v, source.config_source)
        return config

    def write_file(self, filename, attributes=None, owner=None, mode=None):
        config = self._config_dict()
        if not attributes:
            attributes = config.keys()
            attributes.sort()
        if self.install_prefix:
            filename = self.install_prefix + filename
        target_dir = os.path.dirname(filename)
        make_dirs(target_dir, owner=owner)
        fd, tmpname = tempfile.mkstemp(dir=target_dir)
        f = os.fdopen(fd, 'w')
        try:
            for a in attributes:
                f.write('%s=%r\n' % (a, config[a].value))
            f.flush()
            if owner is not None:
                chown(tmpname, owner)
            if mode is not None:
                chmod(tmpname, mode)
            os.rename(tmpname, filename)
        finally:
            f.close()
            try:
                os.unlink(tmpname)
            except OSError:
                pass

    def __repr__(self):
        config = self._config_dict()
        attrs = config.keys()
        attrs.sort()
        attrs = ['\n    %s=%r (from %s)' % (a,config[a].value,config[a].source) 
                 for a in attrs]
        return '<%s%s>' % (self.__class__.__name__, ''.join(attrs))

class Args:
    pass

def args_with_defaults(kwargs, config, arglist, conf_prefix = ''):
    args = Args()
    for argname in arglist:
        try:
            value = kwargs[argname]
        except KeyError:
            try:
                value = getattr(config, conf_prefix + argname)
            except AttributeError:
                try:
                    value = getattr(config, argname)
                except AttributeError:
                    value = None
        setattr(args, argname, value)
    return args
