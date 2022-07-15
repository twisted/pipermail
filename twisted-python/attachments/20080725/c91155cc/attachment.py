import gc
from subprocess import call
from twisted.trial import unittest
from twisted.enterprise import adbapi

TEST_DB_NAME = "TestDB"

class DBConnectionBase(unittest.TestCase):

	def setUp(self):
		# Drop the existing database, if any.
		# We explicitly ignore the return value
		call(["dropdb", "-q", TEST_DB_NAME])
		
		# Recreate the database.
		result = call(["createdb", "-q", TEST_DB_NAME])
		if result != 0:
			# This is the exception raised when the problem occurs.
			raise self.failureException("Could not create database")

		self.db_connection = adbapi.ConnectionPool("psycopg2",
				database=TEST_DB_NAME)

	def tearDown(self):
		# Without this line, the second and subsequent tests fail every time
		# (rather than intermittent failures)
		self.db_connection.close()

		# Uncommenting the following line causes all the problems to go away,
		# but it seems a bit of a sledgehammer for this particular walnut.
		#gc.collect()

	def _run_test(self):
		d = self.db_connection.runQuery("""
				SELECT table_name 
				FROM information_schema.tables 
				WHERE table_schema = 'public'
			""")
		d.addCallback(self.failUnlessEqual, [])

		# A second DB call makes failures more frequent.
		d.addCallback(lambda _: self.db_connection.runQuery("""
				SELECT table_name
				FROM information_schema.views
				WHERE table_schema = 'public'
			"""))
		d.addCallback(self.failUnlessEqual, [])

		return d

	# A hundred test-runs causes the problem to occur about five times, on
	# average. The alternative to this duplication is one test run with 
	# 'trial -u', but the delay between each test pass prevents the problem
	# from occurring
	def test_00(self): return self._run_test()
	def test_01(self): return self._run_test()
	def test_02(self): return self._run_test()
	def test_02(self): return self._run_test()
	def test_03(self): return self._run_test()
	def test_04(self): return self._run_test()
	def test_05(self): return self._run_test()
	def test_06(self): return self._run_test()
	def test_07(self): return self._run_test()
	def test_08(self): return self._run_test()
	def test_09(self): return self._run_test()
	def test_10(self): return self._run_test()
	def test_11(self): return self._run_test()
	def test_12(self): return self._run_test()
	def test_13(self): return self._run_test()
	def test_14(self): return self._run_test()
	def test_15(self): return self._run_test()
	def test_16(self): return self._run_test()
	def test_17(self): return self._run_test()
	def test_18(self): return self._run_test()
	def test_19(self): return self._run_test()
	def test_20(self): return self._run_test()
	def test_21(self): return self._run_test()
	def test_22(self): return self._run_test()
	def test_23(self): return self._run_test()
	def test_24(self): return self._run_test()
	def test_25(self): return self._run_test()
	def test_26(self): return self._run_test()
	def test_27(self): return self._run_test()
	def test_28(self): return self._run_test()
	def test_29(self): return self._run_test()
	def test_30(self): return self._run_test()
	def test_31(self): return self._run_test()
	def test_32(self): return self._run_test()
	def test_33(self): return self._run_test()
	def test_34(self): return self._run_test()
	def test_35(self): return self._run_test()
	def test_36(self): return self._run_test()
	def test_37(self): return self._run_test()
	def test_38(self): return self._run_test()
	def test_39(self): return self._run_test()
	def test_40(self): return self._run_test()
	def test_41(self): return self._run_test()
	def test_42(self): return self._run_test()
	def test_43(self): return self._run_test()
	def test_44(self): return self._run_test()
	def test_45(self): return self._run_test()
	def test_46(self): return self._run_test()
	def test_47(self): return self._run_test()
	def test_48(self): return self._run_test()
	def test_49(self): return self._run_test()
	def test_50(self): return self._run_test()
	def test_51(self): return self._run_test()
	def test_52(self): return self._run_test()
	def test_53(self): return self._run_test()
	def test_54(self): return self._run_test()
	def test_55(self): return self._run_test()
	def test_56(self): return self._run_test()
	def test_57(self): return self._run_test()
	def test_58(self): return self._run_test()
	def test_59(self): return self._run_test()
	def test_60(self): return self._run_test()
	def test_61(self): return self._run_test()
	def test_62(self): return self._run_test()
	def test_63(self): return self._run_test()
	def test_64(self): return self._run_test()
	def test_65(self): return self._run_test()
	def test_66(self): return self._run_test()
	def test_67(self): return self._run_test()
	def test_68(self): return self._run_test()
	def test_69(self): return self._run_test()
	def test_70(self): return self._run_test()
	def test_71(self): return self._run_test()
	def test_72(self): return self._run_test()
	def test_73(self): return self._run_test()
	def test_74(self): return self._run_test()
	def test_75(self): return self._run_test()
	def test_76(self): return self._run_test()
	def test_77(self): return self._run_test()
	def test_78(self): return self._run_test()
	def test_79(self): return self._run_test()
	def test_80(self): return self._run_test()
	def test_81(self): return self._run_test()
	def test_82(self): return self._run_test()
	def test_83(self): return self._run_test()
	def test_84(self): return self._run_test()
	def test_85(self): return self._run_test()
	def test_86(self): return self._run_test()
	def test_87(self): return self._run_test()
	def test_88(self): return self._run_test()
	def test_89(self): return self._run_test()
	def test_90(self): return self._run_test()
	def test_91(self): return self._run_test()
	def test_92(self): return self._run_test()
	def test_93(self): return self._run_test()
	def test_94(self): return self._run_test()
	def test_95(self): return self._run_test()
	def test_96(self): return self._run_test()
	def test_97(self): return self._run_test()
	def test_98(self): return self._run_test()
	def test_99(self): return self._run_test()
