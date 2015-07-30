import pkgutil
import robot.running.context as ctx
from robot.api import TestSuite
from robot.running.keywordrunner import StatusReporter, ErrorDetails, HandlerExecutionFailed
from robot.result.keyword import Keyword as KeywordResult
from robot.running.outputcapture import OutputCapturer
import sys
from robot.utils import ArgumentParser
from robot.run import USAGE
from robot.conf import RobotSettings
from robot.output import LOGGER, Output, pyloggingconf
from robot.running.signalhandler import STOP_SIGNAL_MONITOR
from robot.running.namespace import IMPORTER
from robot.running.runner import Runner, get_timestamp, PassExecution, ModelCombiner, TestStatus
from overrides import overrides

def kw(f):
    def func(*args, **kw):
      result = KeywordResult(kwname=f.__name__, doc=f.__doc__)
      context = ctx.EXECUTION_CONTEXTS.current
      with StatusReporter(context, result):
              try:
                  with OutputCapturer():
                    return f(*args, **kw)
              except Exception:
                   failure = HandlerExecutionFailed(ErrorDetails())
                   context.fail(failure.full_message)
                   if failure.traceback:
                       context.debug(failure.traceback)
                   raise
    return func

def test(*args, **kwargs):
    def test_decorator(f):
        f.is_test = True
        f.tags = kwargs['tags'] if kwargs and 'tags' in kwargs else ()
        return f
    if not kwargs and args and len(args) == 1:
        return test_decorator(args[0])
    return test_decorator

class JudasRunner(Runner):

    def __init__(self, tests, *other):
        Runner.__init__(self, *other)
        self._actual_tests = tests

    @overrides
    def visit_test(self, test):
        t = self._actual_tests[test]
        self._executed_tests[test.name] = True
        result = self._suite.tests.create(name=t.__name__,
                                          doc=t.__doc__,
                                          tags=t.tags,
                                          starttime=get_timestamp(),
                                          timeout=self._get_timeout(test))
        status = TestStatus(self._suite_status, result.critical)
        self._context.start_test(result)
        self._output.start_test(ModelCombiner(result, test))
        try:
            with OutputCapturer():
                t()
        except PassExecution as exception:
            err = exception.earlier_failures
            if err:
                status.test_failed(err)
            else:
                result.message = exception.message
        except Exception as err:
            status.test_failed(err)
        result.status = status.status
        result.message = status.message or result.message
        result.status = status.status
        result.endtime = get_timestamp()
        self._output.end_test(ModelCombiner(result, test))
        self._context.end_test(result)


def runner(datasources, **options):
    tests = _tests(datasources)
    settings = RobotSettings(options)
    rf_test_to_actual, suite = _build_rf_suite(datasources, settings, tests)
    LOGGER.register_console_logger(**settings.console_output_config)
    with pyloggingconf.robot_handler_enabled(settings.log_level):
        with STOP_SIGNAL_MONITOR:
            IMPORTER.reset()
            output = Output(settings)
            runner = JudasRunner(rf_test_to_actual, output, settings)
            suite.visit(runner)
        output.close(runner.result)
    return runner.result


def _tests(datasources):
    for loader, module_name, is_pkg in  pkgutil.iter_modules([datasources[0]]):
        module = loader.find_module(module_name).load_module(module_name)
        for item_name in dir(module):
            item = getattr(module, item_name)
            if hasattr(item, 'is_test') and getattr(item, 'is_test'):
                yield item, module_name


def _build_rf_suite(datasources, settings, tests):
    parent_suite = TestSuite(datasources[0])
    rf_test_to_actual = {}
    current_suite = parent_suite
    for actual_test, module_name in tests:
        if current_suite.name != module_name:
            current_suite = parent_suite.suites.create()
            current_suite.name = module_name
        rf_test = current_suite.tests.create()
        rf_test.name = actual_test.__name__
        rf_test.tags = actual_test.tags
        rf_test_to_actual[rf_test] = actual_test
    parent_suite.configure(**settings.suite_config)
    return rf_test_to_actual, parent_suite


def main(args):
    from robot.api import ResultWriter
    opts, datasources = ArgumentParser(USAGE).parse_args(args)
    keys = set()
    for k in opts:
        if opts[k] is None:
            keys.add(k)
    for k in keys:
        del opts[k]
    opts['dotted'] = True
    runner(datasources, **opts)
    ResultWriter(opts.get('output', 'output.xml')).write_results(settings=None, **opts)


if __name__ == '__main__' :
    main(sys.argv[1:])
