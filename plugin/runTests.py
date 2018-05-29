# Vim fails to correctly add the systempath - so we have to do it manually
import os
import sys
import unittest
import coverage
import importlib
from io import StringIO
from sortedcontainers import SortedSet

try:
    vimMode = True
    import vim
    projectDir = vim.eval("expand('%:p:h')")
    if projectDir not in sys.path:
        sys.path.append(projectDir)
except:
    vimMode = False


def getProjectRoot():
    if '.project' in os.listdir('.'):
        return '.'
    searchPath = '../'
    while 'home' not in os.listdir(searchPath):
        if '.project' in os.listdir(searchPath):
            return searchPath
        searchPath += '../'
    return '.'

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
        except AttributeError:
            pass

def getTestMethodsFromClass(testClass):
    methods = dir(testClass)
    return list(filter(lambda m: m not in dir(unittest.TestCase), methods))

def isTestFile(filename):
    try:
        return filename[:4].lower() == 'test' and filename[-3:] == '.py'
    except:
        return False


class ImportManager:
    def __init__(self):
        self.testModules=[]

    def reloadTestModules(self):
        pass

    def reloadTestClasses(self):
        reloadUserModules()
        filenames = os.listdir('.')
        testFilenames = list(filter(lambda filename: isTestFile(filename), filenames))
        testModuleNames = list(map(lambda filename: filename[:-3], testFilenames))


        self.testModules = []
        for moduleName in testModuleNames:
            try:
                self.testModules.append(importlib.import_module(moduleName))
            except:
                # problem with module it's self
                pass

        self.testClasses = []
        for m in self.testModules:
            self.testClasses += getTestClasses(m)




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
        cov = coverage.coverage()
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

    def clearTests(self):
        self.tests = []

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
            if self.filename in self.passingCoverage.keys():
                for s in self.passingCoverage[self.filename]:
                    vim.command("call s:markSuccess(" + str(s) + ")")
                for s in self.failingCoverage[self.filename]:
                    vim.command("call s:markFailure(" + str(s) + ")")


class TestManager:
    def __init__(self):
        self.importManager = ImportManager()

    def runTests(self):
        testCollection = TestCollection()
        testCollection.clearTests()
        self.importManager.reloadTestClasses()
        for testClass in self.importManager.testClasses:
            tests = getTestMethodsFromClass(testClass)
            for test in tests:
                testCollection.addTest(TestData(testClass, test))
        testCollection.getCoverage()

def getTestClasses(module):
    testClasses = []
    for d in dir(module):
        attr = getattr(module, d)
        try:
            if issubclass(attr, unittest.TestCase):
                testClasses.append(attr)
        except TypeError:
            # attr is not a class
            pass
    return testClasses






