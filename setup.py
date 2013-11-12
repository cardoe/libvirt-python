#!/usr/bin/python

from distutils.core import setup, Extension, Command
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.sdist import sdist
from distutils.dir_util import remove_tree
from distutils.util import get_platform
from distutils.spawn import spawn
import distutils

import sys
import datetime
import os
import os.path
import re
import time

MIN_LIBVIRT = "0.10.2"

pkgcfg = distutils.spawn.find_executable("pkg-config")

if pkgcfg is None:
    raise Exception("pkg-config binary is required to compile libvirt-python")

spawn([pkgcfg,
       "--print-errors",
       "--atleast-version=%s" % MIN_LIBVIRT,
       "libvirt"])

def get_pkgconfig_data(args, mod, required=True):
    """Run pkg-config to and return content associated with it"""
    f = os.popen("%s %s %s" % (pkgcfg, " ".join(args), mod))

    line = f.readline()
    if line is not None:
        line = line.strip()

    if line is None or line == "":
        if required:
            raise Exception("Cannot determine '%s' from libvirt pkg-config file" % " ".join(args))
        else:
            return ""

    return line

ldflags = get_pkgconfig_data(["--libs-only-L"], "libvirt", False)
cflags = get_pkgconfig_data(["--cflags"], "libvirt", False)

module = Extension('libvirtmod',
                   sources = ['libvirt-override.c', 'build/libvirt.c', 'typewrappers.c', 'libvirt-utils.c'],
                   libraries = [ "virt" ],
                   include_dirs = [ "." ])
if cflags != "":
    module.extra_compile_args.append(cflags)
if ldflags != "":
    module.extra_link_args.append(ldflags)


moduleqemu = Extension('libvirtmod_qemu',
                       sources = ['libvirt-qemu-override.c', 'build/libvirt-qemu.c', 'typewrappers.c', 'libvirt-utils.c'],
                       libraries = [ "virt-qemu" ],
                       include_dirs = [ "." ])
if cflags != "":
    moduleqemu.extra_compile_args.append(cflags)
if ldflags != "":
    moduleqemu.extra_link_args.append(ldflags)

modulelxc = Extension('libvirtmod_lxc',
                      sources = ['libvirt-lxc-override.c', 'build/libvirt-lxc.c', 'typewrappers.c', 'libvirt-utils.c'],
                      libraries = [ "virt-lxc" ],
                      include_dirs = [ "." ])
if cflags != "":
    modulelxc.extra_compile_args.append(cflags)
if ldflags != "":
    modulelxc.extra_link_args.append(ldflags)

class my_build(build):

    def get_api_xml_files(self):
        """Check with pkg-config that libvirt is present and extract
        the API XML file paths we need from it"""

        libvirt_api = get_pkgconfig_data(["--variable", "libvirt_api"], "libvirt")

        offset = libvirt_api.index("-api.xml")
        libvirt_qemu_api = libvirt_api[0:offset] + "-qemu-api.xml"

        offset = libvirt_api.index("-api.xml")
        libvirt_lxc_api = libvirt_api[0:offset] + "-lxc-api.xml"

        return (libvirt_api, libvirt_qemu_api, libvirt_lxc_api)


    def run(self):
        apis = self.get_api_xml_files()

        self.spawn(["./generator.py", apis[0], apis[1], apis[2]])

        build.run(self)

class my_sdist(sdist):
    user_options = sdist.user_options

    description = "Update libvirt-python.spec; build sdist-tarball."

    def initialize_options(self):
        self.snapshot = None
        sdist.initialize_options(self)

    def finalize_options(self):
        if self.snapshot is not None:
            self.snapshot = 1
        sdist.finalize_options(self)

    def gen_rpm_spec(self):
        f1 = open('libvirt-python.spec.in', 'r')
        f2 = open('libvirt-python.spec', 'w')
        for line in f1:
            f2.write(line
                     .replace('@PY_VERSION@', self.distribution.get_version())
                     .replace('@C_VERSION@', MIN_LIBVIRT))
        f1.close()
        f2.close()

    def gen_authors(self):
        f = os.popen("git log --pretty=format:'%aN <%aE>'")
        authors = []
        for line in f:
            authors.append("   " + line.strip())

        authors.sort(key=str.lower)

        f1 = open('AUTHORS.in', 'r')
        f2 = open('AUTHORS', 'w')
        for line in f1:
            f2.write(line.replace('@AUTHORS@', "\n".join(authors)))
        f1.close()
        f2.close()


    def gen_changelog(self):
        f1 = os.popen("git log '--pretty=format:%H:%ct %an  <%ae>%n%n%s%n%b%n'")
        f2 = open("ChangeLog", 'w')

        for line in f1:
            m = re.match(r'([a-f0-9]+):(\d+)\s(.*)', line)
            if m:
                t = time.gmtime(int(m.group(2)))
                f2.write("%04d-%02d-%02d %s\n" % (t.tm_year, t.tm_mon, t.tm_mday, m.group(3)))
            else:
                if re.match(r'Signed-off-by', line):
                    continue
                f2.write("    " + line.strip() + "\n")

        f1.close()
        f2.close()


    def run(self):
        if not os.path.exists("build"):
            os.mkdir("build")

        if os.path.exists(".git"):
            try:
                self.gen_rpm_spec()
                self.gen_authors()
                self.gen_changelog()

                sdist.run(self)

            finally:
                files = ["libvirt-python.spec",
                         "AUTHORS",
                         "ChangeLog"]
                for f in files:
                    if os.path.exists(f):
                        os.unlink(f)
        else:
            sdist.run(self)

class my_rpm(Command):
    user_options = []

    description = "Build src and noarch rpms."

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """
        Run sdist, then 'rpmbuild' the tar.gz
        """

        self.run_command('sdist')
        os.system('rpmbuild -ta --clean dist/libvirt-python-%s.tar.gz' %
                  self.distribution.get_version())

class my_test(Command):
    user_options = [
        ('build-base=', 'b',
         "base directory for build library"),
        ('build-platlib=', None,
         "build directory for platform-specific distributions"),
        ('plat-name=', 'p',
         "platform name to build for, if supported "
         "(default: %s)" % get_platform()),
    ]

    description = "Run test suite."

    def initialize_options(self):
        self.build_base = 'build'
        self.build_platlib = None
        self.plat_name = None

    def finalize_options(self):
        if self.plat_name is None:
            self.plat_name = get_platform()

        plat_specifier = ".%s-%s" % (self.plat_name, sys.version[0:3])

        if hasattr(sys, 'gettotalrefcount'):
            plat_specifier += '-pydebug'

        if self.build_platlib is None:
            self.build_platlib = os.path.join(self.build_base,
                                              'lib' + plat_specifier)

    def run(self):
        """
        Run test suite
        """

        self.spawn(["./sanitytest.py", self.build_platlib])


class my_clean(clean):
    def run(self):
        clean.run(self)

        if os.path.exists("build"):
            remove_tree("build")

setup(name = 'libvirt-python',
      version = '1.2.0',
      description = 'The libvirt virtualization API',
      ext_modules = [module, modulelxc, moduleqemu],
      py_modules = ["libvirt", "libvirt_qemu", "libvirt_lxc"],
      package_dir = {
          '': 'build'
      },
      cmdclass = {
          'build': my_build,
          'clean': my_clean,
          'sdist': my_sdist,
          'rpm': my_rpm,
          'test': my_test
      })
