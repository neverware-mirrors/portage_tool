# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from _emerge.CompositeTask import CompositeTask
from _emerge.EbuildPhase import EbuildPhase
from portage import os, xpak

class EbuildBinpkg(CompositeTask):
	"""
	This assumes that src_install() has successfully completed.
	"""
	__slots__ = ('pkg', 'settings') + \
		('_binpkg_tmpfile', '_symbols_tmpfile')

	def _start(self):
		pkg = self.pkg
		root_config = pkg.root_config
		bintree = root_config.trees["bintree"]
		bintree.prevent_collision(pkg.cpv)
		binpkg_tmpfile = os.path.join(bintree.pkgdir,
			pkg.cpv + ".tbz2." + str(os.getpid()))
		bintree._ensure_dir(os.path.dirname(binpkg_tmpfile))

		self._binpkg_tmpfile = binpkg_tmpfile
		self.settings["PORTAGE_BINPKG_TMPFILE"] = self._binpkg_tmpfile

		if 'separatedebug' in self.settings.features:
			self._symbols_tmpfile = os.path.join(bintree.pkgdir, pkg.cpv \
										+ '.debug.tbz2')
			self.settings["PORTAGE_DEBUGSYMBOLS_TMPFILE"] = \
					self._symbols_tmpfile

		package_phase = EbuildPhase(background=self.background,
			phase='package', scheduler=self.scheduler,
			settings=self.settings)

		self._start_task(package_phase, self._package_phase_exit)

	def _package_phase_exit(self, package_phase):

		self.settings.pop("PORTAGE_BINPKG_TMPFILE", None)
		self.settings.pop("PORTAGE_DEBUGSYMBOLS_TMPFILE", None)
		if self._default_exit(package_phase) != os.EX_OK:
			try:
				os.unlink(self._binpkg_tmpfile)
			except OSError:
				pass
			try:
				os.unlink(self._symbols_tmpfile)
			except OSError:
				pass
			self.wait()
			return

		pkg = self.pkg
		if self._symbols_tmpfile and os.path.isfile(self._symbols_tmpfile):
			xpak_data = xpak.xpak_mem({ "CATEGORY": pkg.category,
							  "PF": pkg.pf + "-debug",
							  "SLOT": pkg._metadata['SLOT'] })
			xpak.tbz2(self._symbols_tmpfile).recompose_mem(xpak_data)
		bintree = pkg.root_config.trees["bintree"]
		bintree.inject(pkg.cpv, filename=self._binpkg_tmpfile)

		self._current_task = None
		self.returncode = os.EX_OK
		self.wait()
