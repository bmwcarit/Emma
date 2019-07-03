"""
Emma - Emma Memory and Mapfile Analyser
Copyright (C) 2019 The Emma authors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

# Emma Memory and Mapfile Analyser - command-line tests


import unittest
import sys
import os
import shutil

sys.path.append("../")
import emma
import emma_vis

import shared_libs.emma_helper


class CmdEmma(unittest.TestCase):
    def test_help(self):
        """
        Check that `--help` does not raise an exeption
        """
        # with self.assertRaises(SystemExit):
        try:
            args = emma.parseArgs(["--help"])
            emma.main(args)
        except SystemExit as e:
            if e.code != 0:
                print("Exit code", e.code)
                raise e

    def test_unrecognisedArgs(self):
        """
        Check that `--help` does not raise an exeption
        """
        # with self.assertRaises(SystemExit):
        try:
            args = emma.parseArgs(["--project", "doc/test_project", "--mapfiles", "doc/test_project/mapfiles", "--blahhhhhh"])
            emma.main(args)
        except SystemExit as e:
            if e.code != 2:
                print("Exit code", e.code)
                raise e

    def test_noProjMapfileDir(self):
        with self.assertRaises(SystemExit):
            args = emma.parseArgs(["--project", "this/directory/does/not/exist", "--mapfiles", "this/directory/does/not/exist"])
            emma.main(args)

    @staticmethod
    def test_normalRun():
        """
        Check that an ordinary run is successful
        """
        os.chdir("../")
        args = emma.parseArgs(["--project", "doc/test_project", "--mapfiles", "doc/test_project/mapfiles"])
        emma.main(args)
        os.chdir("tests")


class CmdEmmaVis(unittest.TestCase):
    def test_help(self):
        """
        Check that `--help` does not raise an exeption
        """
        # with self.assertRaises(SystemExit):
        try:
            args = emma_vis.parseArgs(["--help"])
            emma_vis.main(args)
        except SystemExit as e:
            if e.code != 0:
                print("Exit code", e.code)
                raise e

    @staticmethod
    def test_normalRun():
        """
        Check that an ordinary run is successful
        """
        os.chdir("../")
        # args = emma.parseArgs(["--project", "doc/test_project", "--mapfiles", "doc/test_project/mapfiles"])
        # emma.main(args)

        args = emma_vis.parseArgs(["--project", "doc/test_project", "--overview", "--quiet"])
        emma_vis.main(args)
        os.chdir("tests")

    @staticmethod
    def test_runWithNoMemStats():
        """
        No memStats should not raise an exception but exit with sys.exit(-10)
        """
        os.chdir("../")
        tempMemStatsPath = "temp"
        tempMemStatsPathMemStats = shared_libs.emma_helper.joinPath(tempMemStatsPath, "memStats")
        if os.path.isdir(tempMemStatsPathMemStats):
            os.removedirs(tempMemStatsPathMemStats)
        os.makedirs(tempMemStatsPathMemStats)

        # Make sure the directory is empty
        assert len(os.listdir(tempMemStatsPathMemStats)) == 0

        def cleanUp():
            shutil.rmtree(tempMemStatsPath)
            os.chdir("tests")
        try:
            args = emma_vis.parseArgs(["--project", "doc/test_project", "--overview", "--dir", tempMemStatsPath])
            emma_vis.main(args)
        except SystemExit as e:
            if -10 != e.code:
                cleanUp()
                print("Exit code", e.code)
                raise e
            else:
                # All good; program ends with sys.exit(-10) since no file was found
                cleanUp()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.argv.pop()
    unittest.main()
