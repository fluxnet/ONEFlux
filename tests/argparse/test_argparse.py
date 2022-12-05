import unittest
from unittest.mock import patch
import sys
import oneflux
from oneflux.configs.utils import ONEFluxConfig, argparse_from_yaml_and_cli

class TestArgParse(unittest.TestCase):
    def test_argparse_default(self):
        with patch("sys.argv", ["python runoneflux.py"]):
            _, _, args = argparse_from_yaml_and_cli()
        self.assertEqual(args.command, 'all')
        self.assertEqual(args.datadir, './data')
        self.assertEqual(args.siteid, '<replace_me>')
        self.assertEqual(args.sitedir, '<replace_me>')
        self.assertEqual(args.firstyear, 2005)
        self.assertEqual(args.lastyear, 2006)
        self.assertEqual(args.perc, None)
        self.assertEqual(args.prod, None)
        self.assertEqual(args.logfile, 'oneflux.log')
        self.assertEqual(args.forcepy, False)
        self.assertEqual(args.mcr_directory, '<replace_me>/MATLAB_Runtime/v94')
        self.assertEqual(args.recint, 'hh')
        self.assertEqual(args.versionp, oneflux.VERSION_PROCESSING)
        self.assertEqual(args.versiond, oneflux.VERSION_METADATA)
        self.assertEqual(args.erafy, oneflux.pipeline.common.ERA_FIRST_YEAR)
        self.assertEqual(args.eraly, oneflux.pipeline.common.ERA_LAST_YEAR)
        self.assertEqual(args.configfile, None)

    def test_argparse_cli_value(self):
        eraly_val = 3000
        with patch("sys.argv", ["python runoneflux.py",
                                "--era-ly", f"{eraly_val}"]):
            _, _, args = argparse_from_yaml_and_cli()
        self.assertEqual(args.eraly, eraly_val)

    def test_argparse_yaml(self):
        test_yaml_path = './tests/argparse/config.yaml'
        with patch("sys.argv", ["python runoneflux.py",
                                "--configfile", f"{test_yaml_path}"]):
            _, _, args = argparse_from_yaml_and_cli()
        self.assertEqual(args.siteid, 'dummy_siteid')
        self.assertEqual(args.sitedir, 'dummy_sitedir')
        self.assertEqual(args.mcr_directory, 'dummy_mcrdir/MATLAB_Runtime/v94')

    def test_arg_cli_overwrite_yaml(self):
        test_yaml_path = './tests/argparse/config.yaml'
        overwritten_siteid = 'dummy_overwritten_siteid'
        with patch("sys.argv", ["python runoneflux.py",
                                "--siteid", f"{overwritten_siteid}",
                                "--configfile", f"{test_yaml_path}"]):
            _, _, args = argparse_from_yaml_and_cli()
        self.assertEqual(args.siteid, overwritten_siteid)
        self.assertEqual(args.sitedir, 'dummy_sitedir')
        self.assertEqual(args.mcr_directory, 'dummy_mcrdir/MATLAB_Runtime/v94')
