import unittest
import sys
sys.path.append('../plugin')
import runTests


passingTest = '''import unittest
class TestTemp(unittest.TestCase):
    def test_passing(self):
        self.assertTrue(1==1)'''

failingTest = '''import unittest
class TestTemp(unittest.TestCase):
    def test_failing:
        self.assertTrue(1==0)'''


def writeTempTestFile(s):
    f = open('test_temp.py', 'w')
    f.write(s)

class ImportManagerTests(unittest.TestCase):
    def test_LoadTestModule(self):
        im = runTests.ImportManager()
        writeTempTestFile(passingTest)
        im.reloadTestClasses()
        tempTestModules = list(map(lambda m:m.__name__, im.testModules))
        tempTestClasses = list(filter(lambda c: c.__module__ == 'test_temp', im.testClasses))
        self.assertIn('test_temp', tempTestModules)
        self.assertEquals(len(tempTestClasses),1)

    def test_PassingTest(self):
        tc = runTests.TestCollection()
        im = runTests.ImportManager()
        writeTempTestFile(passingTest)
        im.reloadTestClasses()

    def test_FailingTest(self):
        writeTempTestFile(failingTest)

    def TestPassingTestAfterFailingTest(self):
        writeTempTestFile(failingTest)
        writeTempTestFile(passingTest)


    def TestFailingTestAfterPassingTest(self):
        writeTempTestFile(passingTest)
        writeTempTestFile(failingTest)

if __name__=='__main__':
    unittest.main()
    tc = runTests.TestCollection()
    im = runTests.ImportManager()
    writeTempTestFile(passingTest)
    im.reloadTestClasses()
    print(im.testModules)
    print(im.testClasses)


