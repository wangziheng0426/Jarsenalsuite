
import os
import sipconfig
import PyQt4.pyqtconfig as pyqtconfig
import sys
import getopt
import glob

opt_static=0
opt_debug=0
opt_generate_code=1

class AbsubmitModuleMakefile(pyqtconfig.QtCoreModuleMakefile):
	"""The Makefile class for modules that %Import QtXml.
	"""
	def __init__(self, *args, **kw):
		"""Initialise an instance of a module Makefile.
		"""
		if not kw.has_key("qt"):
			kw["qt"] = ["QtCore", "QtXml", "QtSql","QtNetwork","QtGui"]
			
		apply(pyqtconfig.QtCoreModuleMakefile.__init__, (self, ) + args, kw)
		
	# Override target for static builds
	def finalise(self):
		pyqtconfig.QtCoreModuleMakefile.finalise(self)
		if self.static:
			self._target = 'py' + self._target

def doit():
	global opt_static
	global opt_debug
	global opt_generate_code
	
	# The name of the SIP build file generated by SIP and used by the build
	# system.
	build_file = "absubmit.sbf"

	# Get the PyQt configuration information.
	config = pyqtconfig.Configuration()
	config.pyqt_modules = []
	config.__dict__["AR"] = "ar r"

	# Get the extra SIP flags needed by the imported qt module.  Note that
	# this normally only includes those flags (-x and -t) that relate to SIP's
	# versioning system.
#	qt_sip_flags = config.pyqt_qt_sip_flags

	# Run SIP to generate the code.  Note that we tell SIP where to find the qt
	# module's specification files using the -I flag.
	#config.pyqt_sip_dir = "/usr/share/sip/PyQt4"
	#config.pyqt_sip_dir = "c:\\python24\\sip\\PyQt4\\"
	print config.default_sip_dir
	qt_sip_flags = config.pyqt_sip_flags
	if opt_generate_code:
		if sys.platform=="win32":
				sip_bin = "..\\sip\\sipgen\\sip.exe"
		else:
				sip_bin = config.sip_bin
		if not os.path.exists("sipAbsubmit"):
				os.mkdir("sipAbsubmit")
		ret = os.system(" ".join([sip_bin, "-k", "-c", "sipAbsubmit", "-b", "sipAbsubmit/" + build_file, "-I", config.pyqt_sip_dir, "-I", config.default_sip_dir, "-I", config.sip_mod_dir, config.pyqt_sip_flags, "sip/absubmit.sip"]))
		if ret:
			sys.exit(ret%255)
	
	# Create the Makefile.  The QtModuleMakefile class provided by the
	# pyqtconfig module takes care of all the extra preprocessor, compiler and
	# linker flags needed by the Qt library.
	makefile = AbsubmitModuleMakefile(
		configuration=config,
		build_file=build_file,
		static=opt_static,
		debug=opt_debug,
		# Use the sip mod dir to adhere to the DESTDIR env var
		install_dir=os.path.join(config.sip_mod_dir,"blur"),
#		install_dir=os.path.join(config.default_mod_dir,"blur"),
		dir="sipAbsubmit"
	)

	installs = []
	sipfiles = []

	for s in glob.glob("sip/*.sip"):
		sipfiles.append(os.path.join("sip", os.path.basename(s)))

	installs.append([sipfiles, os.path.join(config.default_sip_dir, "blur")])

	# Use the sip mod dir to adhere to the DESTDIR env var
	#installs.append(["absubmitconfig.py", config.sip_mod_dir])
	#installs.append(["absubmitconfig.py", config.default_mod_dir])

	sipconfig.ParentMakefile(
		configuration=config,
		installs=installs,
		subdirs=["sipAbsubmit"]
	).generate()

	# Add the library we are wrapping.  The name doesn't include any platform
	# specific prefixes or extensions (e.g. the "lib" prefix on UNIX, or the
	# ".dll" extension on Windows).
	if sys.platform == "win32":
		makefile.extra_libs = ["absubmit","classes","stone","QtSql4","QtXml4","QtNetwork4","Mpr"]
	elif sys.platform == "darwin":
		makefile.extra_libs = ["absubmit","classes","stone","absubmit"]
	else:
		makefile.extra_libs = ["absubmit","classes","stone","QtSql","QtXml","QtNetwork","absubmit"]

	makefile.extra_include_dirs = ["../.out","../../stone/include","../include","../../classes/autocore","../../classes"]
	makefile.extra_lib_dirs.append( ".." );
	makefile.extra_lib_dirs.append( "../../stone" );
	makefile.extra_lib_dirs.append( "../../classes" );
	

	# Generate the Makefile itself.
	makefile.generate()

	# Now we create the configuration module.  This is done by merging a Python
	# dictionary (whose values are normally determined dynamically) with a
	# (static) template.
	content = {
		# Publish where the SIP specifications for this module will be
		# installed.
		"stone_sip_dir":    config.default_sip_dir,

		# Publish the set of SIP flags needed by this module.  As these are the
		# same flags needed by the qt module we could leave it out, but this
		# allows us to change the flags at a later date without breaking
		# scripts that import the configuration module.
		"stone_sip_flags":  qt_sip_flags
	}

	# This creates the helloconfig.py module from the helloconfig.py.in
	# template and the dictionary.
	# sipconfig.create_config_module("absubmitconfig.py", "absubmitconfig.py.in", content)

def usage(rcode = 2):
	"""Display a usage message and exit.

	rcode is the return code passed back to the calling process.
	"""
	print "Usage:"
	print "    python configure.py [-k]"
	print "where:"
	print "  -h      display this help message"
	print "  -k      build the PyQt modules as static libraries"
	print "  -n      Dont generate the code with sip, only create the makefiles"
	print "  -u      Debug build"
	sys.exit(rcode)

def main(argv):
	"""Create the configuration module module.

	argv is the list of command line arguments.
	"""

	# Parse the command line.
	try:
		optlist, args = getopt.getopt(argv[1:], "khnu")
	except getopt.GetoptError:
		usage()

	global opt_static
	global opt_generate_code
	global opt_debug
	
	for opt, arg in optlist:
		if opt == "-h":
			usage(0)
		elif opt == "-k":
			opt_static = 1
		elif opt == "-n":
			opt_generate_code = 0;
		elif opt == "-u":
			opt_debug = 1
	doit()

if __name__ == "__main__":
	try:
		main(sys.argv)
	except SystemExit:
		raise
	except:
		print \
"""An internal error occured.  Please report all the output from the program,
including the following traceback, to support@riverbankcomputing.co.uk.
"""
		raise
