Index: twisted/scripts/trial.py
===================================================================
RCS file: /cvs/Twisted/twisted/scripts/trial.py,v
retrieving revision 1.44
diff -c -r1.44 trial.py
*** twisted/scripts/trial.py	2 Jun 2003 15:46:26 -0000	1.44
--- twisted/scripts/trial.py	10 Jun 2003 21:44:49 -0000
***************
*** 40,45 ****
--- 40,46 ----
      optParameters = [["reactor", "r", None,
                        "The Twisted reactor to install before running the tests (looked up as a module contained in twisted.internet)"],
                       ["logfile", "l", "test.log", "log file name"],
+                      ["benchmark", None, None, "Benchmark a test by repeating it a specified number of times"],
                       ["random", "z", None,
                        "Run tests in random order using the specified seed"],
                       ["extra","x", None,
***************
*** 54,59 ****
--- 55,61 ----
          self['testcases'] = []
          self['methods'] = []
          self['_couldNotImport'] = {}
+         self['iterations'] = 1
  
      def opt_reactor(self, reactorName):
          # this must happen before parseArgs does lots of imports
***************
*** 123,128 ****
--- 125,140 ----
          import gc
          gc.disable()
  
+     def opt_benchmark(self, iterations):
+         """Benchmark a test/tests by running it a number of times"""
+         try:
+             self['iterations']=int(iterations)
+         except ValueError:
+             raise usage.UsageError("Argument to --benchmark must be a positive integer")
+         if self.iterations<1:
+             raise usage.UsageError("Argument to --benchmark must be a positive integer")
+ 
+ 
      opt_m = opt_module
      opt_p = opt_package
      opt_c = opt_testcase
***************
*** 246,252 ****
         log.addObserver(seeWarnings)
         log.startLogging(open(config['logfile'], 'a'), 0)
  
!     if config['verbose']:
          reporter = reps.TreeReporter(sys.stdout)
      elif config['bwverbose']:
          reporter = reps.VerboseTextReporter(sys.stdout)
--- 258,266 ----
         log.addObserver(seeWarnings)
         log.startLogging(open(config['logfile'], 'a'), 0)
  
!     if config['iterations']>1:
!         reporter = reps.BenchmarkTextReporter(sys.stdout)
!     elif config['verbose']:
          reporter = reps.TreeReporter(sys.stdout)
      elif config['bwverbose']:
          reporter = reps.VerboseTextReporter(sys.stdout)
***************
*** 286,297 ****
          import profile
          prof = profile.Profile()
          try:
!             prof.runcall(suite.run, reporter, config['random'])
          except SystemExit:
              pass
          prof.print_stats()
      else:
!         suite.run(reporter, config['random'])
      sys.exit(not reporter.allPassed())
  
  if __name__ == '__main__':
--- 300,311 ----
          import profile
          prof = profile.Profile()
          try:
!             prof.runcall(suite.run, reporter, config['random'], config['iterations'])
          except SystemExit:
              pass
          prof.print_stats()
      else:
!         suite.run(reporter, config['random'], config['iterations'])
      sys.exit(not reporter.allPassed())
  
  if __name__ == '__main__':
Index: twisted/trial/reporter.py
===================================================================
RCS file: /cvs/Twisted/twisted/trial/reporter.py,v
retrieving revision 1.10
diff -c -r1.10 reporter.py
*** twisted/trial/reporter.py	18 May 2003 06:30:07 -0000	1.10
--- twisted/trial/reporter.py	10 Jun 2003 21:44:52 -0000
***************
*** 242,247 ****
--- 242,302 ----
          self.writeln(words.get(resultType, "[??]")+" "+"(%.02f secs)" % t)
          Reporter.reportResults(self, testClass, method, resultType, results)
  
+ class BenchmarkTextReporter(TextReporter):
+     def __init__(self, stream=sys.stdout):
+         self.lasttest=None
+         self.timesum=0
+         self.iteration=0
+         self.error=0
+         TextReporter.__init__(self, stream)
+ 
+     def reportStart(self, testClass, method):
+         if self.lasttest and self.lasttest != (testClass, method):
+             self.reportTestResults()
+             self.timesum=self.iteration=0
+             self.error=0
+         self.lasttest=(testClass, method)
+         self.testStartedAt = time.time()
+         if not self.iteration:
+             self.write('%s (%s) ... ', method.__name__, reflect.qual(testClass))
+     
+     def reportResults(self, testClass, method, resultType, results=None):
+         stopped = time.time()
+         t = stopped-self.testStartedAt
+         self.timesum+=t
+         self.iteration+=1
+         if resultType!=SUCCESS:
+             self.error=resultType
+         self.results=results
+ 
+     def stop(self):
+         # ensure the final test is reported
+         if self.lasttest:
+             self.reportTestResults()
+             self.lasttest=None
+         self.timesum=self.iteration=self.error=0
+         TextReporter.stop(self)
+ 
+     def reportTestResults(self):
+         if self.error:
+             self.reportErrorResult()
+         else:
+             self.reportGoodResult()
+ 
+     def reportErrorResult(self):
+         words = {SKIP: '[SKIPPED]',
+                  EXPECTED_FAILURE: '[TODO]',
+                  FAILURE: '[FAIL]', ERROR: '[ERROR]',
+                  UNEXPECTED_SUCCESS: '[SUCCESS!?!]',
+                  SUCCESS: '[OK]'}
+         self.writeln(words.get(self.error, "[??]"))
+         Reporter.reportResults(self, self.lasttest[0], self.lasttest[1], self.error, self.results)
+ 
+     def reportGoodResult(self):
+         self.writeln("[OK] (%d passes in %.01f secs; %.02f ms/pass)" % 
+             (self.iteration, self.timesum, self.timesum/self.iteration*1000))
+         Reporter.reportResults(self, self.lasttest[0], self.lasttest[1], SUCCESS, self.results)
+ 
  class VerboseTextReporter(TextReporter):
      def __init__(self, stream=sys.stdout):
          TextReporter.__init__(self, stream)
Index: twisted/trial/runner.py
===================================================================
RCS file: /cvs/Twisted/twisted/trial/runner.py,v
retrieving revision 1.4
diff -c -r1.4 runner.py
*** twisted/trial/runner.py	10 Jun 2003 01:28:33 -0000	1.4
--- twisted/trial/runner.py	10 Jun 2003 21:44:52 -0000
***************
*** 60,72 ****
          assert method.__name__ == self.methodName
          method()
  
!     def runTests(self, output):
          testCase = self.testClass()
          method = getattr(testCase, self.methodName)
!         output.reportStart(self.testClass, method)
!         tester = unittest.Tester(self.testClass, testCase, method, self.runTest)
!         results = tester.run()
!         output.reportResults(self.testClass, method, *results)
  
  
  class TestClassRunner:
--- 60,73 ----
          assert method.__name__ == self.methodName
          method()
  
!     def runTests(self, output, iterations = 1):
          testCase = self.testClass()
          method = getattr(testCase, self.methodName)
!         for x in xrange(iterations):
!             output.reportStart(self.testClass, method)
!             tester = unittest.Tester(self.testClass, testCase, method, self.runTest)
!             results = tester.run()
!             output.reportResults(self.testClass, method, *results)
  
  
  class TestClassRunner:
***************
*** 98,112 ****
          assert method.__name__ in self.methodNames
          method()
  
!     def runTests(self, output):
          self.testCase = self.testClass()
          self.testCase.setUpClass()
          for methodName in self.methodNames:
              method = getattr(self.testCase, methodName)
!             output.reportStart(self.testClass, method)
!             results = unittest.Tester(self.testClass, self.testCase,
!                                       method, self.runTest).run()
!             output.reportResults(self.testClass, method, *results)
          self.testCase.tearDownClass()
  
  def runTest(method):
--- 99,114 ----
          assert method.__name__ in self.methodNames
          method()
  
!     def runTests(self, output, iterations = 1):
          self.testCase = self.testClass()
          self.testCase.setUpClass()
          for methodName in self.methodNames:
              method = getattr(self.testCase, methodName)
!             for x in xrange(iterations):
!                 output.reportStart(self.testClass, method)
!                 results = unittest.Tester(self.testClass, self.testCase,
!                                           method, self.runTest).run()
!                 output.reportResults(self.testClass, method, *results)
          self.testCase.tearDownClass()
  
  def runTest(method):
Index: twisted/trial/unittest.py
===================================================================
RCS file: /cvs/Twisted/twisted/trial/unittest.py,v
retrieving revision 1.75
diff -c -r1.75 unittest.py
*** twisted/trial/unittest.py	10 Jun 2003 01:28:33 -0000	1.75
--- twisted/trial/unittest.py	10 Jun 2003 21:44:54 -0000
***************
*** 290,296 ****
          packageDir = os.path.dirname(package.__file__)
          os.path.walk(packageDir, self._packageRecurse, None)
  
!     def run(self, output, seed = None):
          output.start(self.numTests)
          tests = self.tests
          tests.sort(lambda x,y: cmp(str(x), str(y)))
--- 290,296 ----
          packageDir = os.path.dirname(package.__file__)
          os.path.walk(packageDir, self._packageRecurse, None)
  
!     def run(self, output, seed = None, iterations = 1):
          output.start(self.numTests)
          tests = self.tests
          tests.sort(lambda x,y: cmp(str(x), str(y)))
***************
*** 304,310 ****
              output.writeln('Running tests shuffled with seed %d' % seed)
  
          for test in tests:
!             test.runTests(output)
          
          for name, exc in self.couldNotImport.items():
              output.reportImportError(name, exc)
--- 304,310 ----
              output.writeln('Running tests shuffled with seed %d' % seed)
  
          for test in tests:
!             test.runTests(output, iterations)
          
          for name, exc in self.couldNotImport.items():
              output.reportImportError(name, exc)

