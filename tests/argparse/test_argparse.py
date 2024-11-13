import unittest
from unittest.mock import patch
import sys
import yaml
import oneflux
from oneflux.configs.utils import ONEFluxConfig, argparse_from_yaml_and_cli
from oneflux.tools.partition_nt import PROD_TO_COMPARE, PERC_TO_COMPARE

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

    def test_arg_cli_wrong_args(self):
        wrong_arg = 'wrong_arg'
        wrong_arg_value = 'wrong_arg_value'
        test_yaml_path = './tests/argparse/config.yaml'
        with patch("sys.argv", ["python runoneflux.py",
                                f"--{wrong_arg}", f"{wrong_arg_value}",
                                "--configfile", f"{test_yaml_path}"]):
            with self.assertRaises(SystemExit):
                _, _, args = argparse_from_yaml_and_cli()

    def test_arg_yaml_wrong_args(self):
        test_yaml_path = './tests/argparse/config_faulty.yaml'
        with patch("sys.argv", ["python runoneflux.py",
                                "--configfile", f"{test_yaml_path}"]):
            with self.assertRaises(ValueError):
                _, _, args = argparse_from_yaml_and_cli()

    def test_onefluxconfig_args(self):
        test_yaml_path = './tests/argparse/config.yaml'
        with patch("sys.argv", ["python runoneflux.py",
                                "--configfile", f"{test_yaml_path}"]):
            onefluxconfig = ONEFluxConfig()
        self.assertEqual(onefluxconfig.perc, PERC_TO_COMPARE)
        self.assertEqual(onefluxconfig.prod, PROD_TO_COMPARE)

    def test_onefluxconfig_export_to_yaml(self):
        dir = './tests/argparse'
        yaml_filename = 'config.yaml'
        output_yaml_filename = 'output_config.yaml'
        test_yaml_path = f'{dir}/{yaml_filename}'
        test_output_yaml_path = f'{dir}/{output_yaml_filename}'
        with patch("sys.argv", ["python runoneflux.py",
                                "--configfile", test_yaml_path]):
            onefluxconfig = ONEFluxConfig()
            onefluxconfig.export_to_yaml(dir,
                                         output_yaml_filename,
                                         overwritten=True)
        with open(test_output_yaml_path) as f:
            conf = yaml.safe_load(f)
        self.assertEqual(conf['run']['configfile'], onefluxconfig.args.configfile)
        self.assertEqual(conf['run']['era_fy'], onefluxconfig.args.erafy)
        self.assertEqual(conf['run']['era_ly'], onefluxconfig.args.eraly)
        self.assertEqual(conf['run']['mcr'], onefluxconfig.args.mcr_directory)
        self.assertEqual(conf['run']['sitedir'], onefluxconfig.args.sitedir)
        self.assertEqual(conf['run']['siteid'], onefluxconfig.args.siteid)
        self.assertEqual(conf['run']['versiond'], onefluxconfig.args.versiond)
        self.assertEqual(conf['run']['versionp'], onefluxconfig.args.versionp)

        with patch("sys.argv", ["python runoneflux.py",
                                "--configfile", test_output_yaml_path]):
            new_onefluxconfig = ONEFluxConfig()

        no_check_args_list = ['timestamp', 'configfile']
        for name, val in onefluxconfig.args._get_kwargs():
            if name not in no_check_args_list:
                self.assertEqual(val,
                                 new_onefluxconfig.args.__getattribute__(name))