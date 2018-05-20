# Vim fails to correctly add the systempath - so we have to do it manually
import os
import sys
import unittest
import coverage
import importlib
from io import StringIO
from sortedcontainers import SortedSet

try:
    import vim
    sys.path.append(vim.eval('g:plugindir'))
    sys.path.append(vim.eval("expand('%:p:h')"))
    vimMode = True
except:
    vimMode = False
    print('not vim mode')


def shouldReload(filePath):
    if 'home' not in filePath:
        # not a system module
        return False
    elif 'vim-liveunittest' in filePath:
        # debugging
        return True
    elif '.vim' in filePath:
        # could be another vim plugin. don't intefere
        return False
    else:
        # user code
        return True


def reloadUserModules():
    for m in sys.modules.values():
        try:
            if shouldReload(m.__file__):
                importlib.reload(m)
            #    vim.command("echo '" + str(m.__file__) + " reloaded'")
            #elif 'home' in m.__file__ and 'YouCompleteMe' not in m.__file__:
            #    vim.command("echo '" + str(m.__file__) + " ignored'")

        except AttributeError:
            pass



def isTestFile(filename):
    try:
        return filename[:4].lower() == 'test' and filename[-3:] == '.py'
    except:
        return False


class ImportManager:
    def __init__(self):
        self.testModules=[]

    def reloadTestClasses(self):
        filenames = os.listdir('.')
        testFilenames = list(filter(lambda filename: isTestFile(filename), filenames))
        testModuleNames = list(map(lambda filename: filename[:-3], testFilenames))

        reloadUserModules()

        self.testModules = []
        for moduleName in testModuleNames:
            try:
                self.testModules.append(importlib.import_module(moduleName))
            except:
                pass

        self.testClasses = unittest.TestCase.__subclasses__()
        self.testClasses = list(filter(lambda c: c.__module__ in testModuleNames, self.testClasses))


    def getTestMethodsFromClass(self, testClass):
        methods = dir(testClass)
        return list(filter(lambda m: m not in dir(unittest.TestCase), methods))


class TestData:
    """ TestData holds all the data we wish to know for a given test. From the TestData objects we can almost entirely recreate the state of the program. 
    Attributes:
        testClass and testName refer to the actual test
        coveredFiles, coveredLines and result refer to the state of the test
    Methods:
        Run: (re)runs the test
    """
    def __init__(self, testClass, testName):
        """
        args:
            a testClass object and a string testName
        """
        self.testClass = testClass
        self.testName = testName
        self.run()

    def run(self):
        ''' Runs the particular test. populates self.coveredLines, self.coveredFiles and self.Result which together determine the coverage and status of the test. '''

        # setup
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream)
        suite = unittest.TestSuite()
        suite.addTest(self.testClass(self.testName))

        # Start logging coverage and
        cov = coverage.Coverage()
        cov.start()
        result = runner.run(suite)
        cov.save()

        # todo - analyse and reduce object size
        '''print cov.data.lines(cov.data.measured_files()[0])
        print('Tests run ', result.testsRun)
        print('Passes', result.wasSuccessful())
        print('Failures', result.failures)
        print('Errors ', result.errors)'''
        self.coveredFiles = cov.data.measured_files()
        self.coveredLines = cov.data.lines
        self.result = result


class TestCollection:

    def __init__(self):
        self.tests = []

        if vimMode:        
            self.length = int(vim.eval("line('$')"))
            self.filename =vim.eval("g:filename")
        else:
            self.length = 100

    def addTest(self, test):
        self.tests.append(test)

    def getCoverage(self):
        self.passingCoverage = {}
        self.failingCoverage = {}
        self.exceptionCoverage = {}
        self.notCovered = {}
        for test in self.tests:
            test.run()
            for f in test.coveredFiles:
                if f not in self.passingCoverage:
                    self.passingCoverage[f] = SortedSet()
                    self.failingCoverage[f] = SortedSet()
                    self.notCovered[f] = SortedSet()
                for coveredLine in test.coveredLines(f):
                    if test.result.wasSuccessful():
                        self.passingCoverage[f].add(coveredLine)
                    else:
                        self.failingCoverage[f].add(coveredLine)
                for line in range(self.length):
                    if line not in self.passingCoverage[f] and line not in self.failingCoverage[f]:
                        self.notCovered[f].add(line)


        if vimMode:
            vim.command("sign unplace *")
            for s in self.passingCoverage[self.filename]:
                vim.command("call s:markSuccess(" + str(s) + ")")
            for s in self.failingCoverage[self.filename]:
                vim.command("call s:markFailure(" + str(s) + ")")
                vim.command("echo '" + str(s) + "failed'")


class TestManager:
    def __init__(self):
        self.importManager = ImportManager()


    def runTests(self):
        self.testCollection = TestCollection()
        self.importManager.reloadTestClasses()
        for testClass in self.importManager.testClasses:
            tests = self.importManager.getTestMethodsFromClass(testClass)
            for test in tests:
                self.testCollection.addTest(TestData(testClass, test))
        self.testCollection.getCoverage()


if __name__ == '__main__':
    tm = TestManager()



