# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from _emerge.SlotObject import SlotObject
import portage
from portage import os
from portage.dbapi._MergeProcess import MergeProcess
from portage.dbapi.vartree import dblink

class EbuildMerge(SlotObject):

	__slots__ = ("find_blockers", "logger", "ldpath_mtimes",
		"pkg", "pkg_count", "pkg_path", "pretend",
		"scheduler", "settings", "tree", "world_atom")

	def create_task(self):
		root_config = self.pkg.root_config
		settings = self.settings
		mycat = settings["CATEGORY"]
		mypkg = settings["PF"]
		pkgloc = settings["D"]
		infloc = os.path.join(settings["PORTAGE_BUILDDIR"], "build-info")
		myroot = root_config.root
		myebuild = settings["EBUILD"]
		mydbapi = root_config.trees[self.tree].dbapi
		vartree = root_config.trees["vartree"]
		background = (settings.get('PORTAGE_BACKGROUND') == '1')
		logfile = settings.get('PORTAGE_LOG_FILE')

		merge_task = MergeProcess(
			dblink=dblink, mycat=mycat, mypkg=mypkg, settings=settings,
			treetype=self.tree, vartree=vartree, scheduler=self.scheduler,
			background=background, blockers=self.find_blockers, pkgloc=pkgloc,
			infloc=infloc, myebuild=myebuild, mydbapi=mydbapi,
			prev_mtimes=self.ldpath_mtimes, logfile=logfile)
		merge_task.addExitListener(self._log_exit)
		return merge_task

	def _log_exit(self, task):
		if task.returncode != os.EX_OK:
			return

		pkg = self.pkg
		self.world_atom(pkg)
		pkg_count = self.pkg_count
		pkg_path = self.pkg_path
		logger = self.logger
		if "noclean" not in self.settings.features:
			short_msg = "emerge: (%s of %s) %s Clean Post" % \
				(pkg_count.curval, pkg_count.maxval, pkg.cpv)
			logger.log((" === (%s of %s) " + \
				"Post-Build Cleaning (%s::%s)") % \
				(pkg_count.curval, pkg_count.maxval, pkg.cpv, pkg_path),
				short_msg=short_msg)
		logger.log(" ::: completed emerge (%s of %s) %s to %s" % \
			(pkg_count.curval, pkg_count.maxval, pkg.cpv, pkg.root))

