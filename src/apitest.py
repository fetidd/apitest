import argparse
import os
import subprocess
import sys
import time
import traceback
from copy import deepcopy

import requests
import yaml

from utils import cprint, deep_merge_dicts, colorise, header
import dotenv

TEST_ORDER = ("health", "transaction")

class Test:
    def __init__(self, *, name, section, expected, path="/", method="GET", json=None, description=""):
        self.name = name
        self.section = section
        self.path = path
        self.method = method
        self.json = json
        self.description = description
        self.expected = expected
        self.result = {}

    def __str__(self):
        return "{}: {}".format(self.name, self.result if self.result else "No issues!")
    
    def as_dict(self):
        return {
            "name": self.name,
            "section": self.section[0],
            # "description": self.description,
            # "path": self.path,
            # "method": self.method,
            # "json": self.json,
            # "expected": self.expected,
            "result": self.result
        }

def create_tests(path):
    cprint("dark_gray", "getting tests from {}... ".format(path))
    with open(path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)
    tests = []
    found = 0
    for section_name in TEST_ORDER:
        section = (section_name, [])
        if section_data := data.get(section_name, {}):
            _defaults = section_data.get("defaults", {})
            section_tests = section_data["cases"]
            for test_dict in section_tests:
                defaults = deepcopy(_defaults)
                
                iter_copy = deepcopy(test_dict) # TODO make this a tidier function
                for json_key in iter_copy.get("json", {}):
                    if test_dict["json"][json_key] is None and "json" in defaults:
                        defaults["json"].pop(json_key, None)
                        test_dict["json"].pop(json_key, None)
                for exp_key in iter_copy.get("expected", {}):
                    if exp_key == "json":
                        json_val = iter_copy["expected"].get("json", {})
                        if json_val is not None:
                            for json_key in json_val:
                                if test_dict["expected"]["json"][json_key] is None and "json" in defaults:
                                    defaults["expected"]["json"].pop(json_key, None)
                                    test_dict["expected"]["json"].pop(json_key, None)
                    if test_dict["expected"][exp_key] is None and "expected" in defaults:
                        defaults["expected"].pop(exp_key, None)
                        test_dict["expected"].pop(exp_key, None)
                        
                
                test_dict = deep_merge_dicts(defaults, test_dict)
                test = Test(section=section, **test_dict)
                section[1].append(test)
                found += 1
        tests.append(section)
    cprint("dark_gray", "found {} test(s)!\n".format(found))
    return tests

def run_tests(tests):
    issues: list[Test] = []
    success: list[Test] = []
    for section_name, tests in tests:
        if not tests:
            continue
        # subheader(section_name, "blue")
        with requests.Session() as session:
            for test in tests:
                is_issue = run_test(test, session)
                if is_issue:
                    issues.append(test)
                else:
                    success.append(test)
    return success, issues

def run_test(test: Test, session: requests.Session):
    exp = test.expected
    request_kw = {}
    if test.json:
        request_kw["json"] = test.json
    fn = getattr(session, test.method.lower())
    res = fn("http://localhost:8080" + test.path, **request_kw)
    is_issue = False
    if "status_code" in exp:
        if exp["status_code"] != res.status_code:
            test.result["status_code"] = "{} != {}".format(exp["status_code"], res.status_code)
            is_issue = True
    if exp_json := exp.get("json"):
        try:
            returned_json = res.json()
        except Exception:
            returned_json = None
        if exp_json != returned_json:
            test.result["json"] = returned_json
            test.result["expected_json"] = exp_json
            is_issue = True
    print("{}: {}".format(colorise("red" if is_issue else "green", test.name), test.description[:50]))
    if is_issue:
        print(colorise("dark_grey", yaml.dump(test.result)), end="")
    return is_issue

def main(args):
    all_issues = []
    all_success = []
    try:
        popen_kw = {
            "env": {
                "DATABASE_NAME": "account"
            }
        }
        if not args.verbose:
            popen_kw["stdout"] = open(os.devnull, 'wb')
            popen_kw["stderr"] = open(os.devnull, 'wb')
        server = subprocess.Popen(args.bin, **popen_kw)
        time.sleep(0.5)
        tests = create_tests(args.test_path)
        success, issues = run_tests(tests)
        all_success.extend(success)
        all_issues.extend(issues)
        server.terminate()
    except Exception as e: # something has happened not related to an actual test result
        header("ERROR", "magenta")
        cprint("red", "\n".join(traceback.format_tb(e.__traceback__)))
        cprint("red", e)
        process_name = args.bin.split("/")[-1]
        cprint("dark_gray", "attempting to kill all {} processes...".format(process_name))
        subprocess.run(["killall", process_name]) # kill the process because we won't have hit the terminate
        sys.exit(1)
    if all_issues:
        header(f"{len(all_issues)} FAILED", "red")
        if args.verbose:
            for issue in all_issues:
                cprint("yellow", yaml.dump(issue.as_dict()))
        print()
        sys.exit(1)
    else:
        header("SUCCESSFUL", "green")
        if args.verbose:
            for success in all_success:
                cprint("green", success)
        print()
        sys.exit(0)
        
def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

if __name__ == "__main__":
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", action="store", default=os.getenv("BIN_PATH", "{}/testBuild".format(get_script_path())))
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--test_path", action="store", default=os.getenv("TEST_PATH", "{}/tests.yaml".format(get_script_path())))
    args = parser.parse_args(sys.argv[1:])
    print()
    main(args)
