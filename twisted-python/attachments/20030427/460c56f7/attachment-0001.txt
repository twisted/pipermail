Index: twisted/enterprise/reflector.py
===================================================================
RCS file: /cvs/Twisted/twisted/enterprise/reflector.py,v
retrieving revision 1.15
diff -u -r1.15 reflector.py
--- twisted/enterprise/reflector.py	12 Feb 2003 14:37:48 -0000	1.15
+++ twisted/enterprise/reflector.py	27 Apr 2003 18:05:15 -0000
@@ -18,7 +18,7 @@
 import weakref
 
 from twisted.enterprise import adbapi
-from twisted.enterprise.util import DBError, getKeyColumn, quote, _TableInfo, _TableRelationship
+from twisted.enterprise.util import DBError, getKeyColumn, _TableInfo, _TableRelationship
 from twisted.enterprise.row import RowObject
 from twisted.internet import defer
 
Index: twisted/enterprise/row.py
===================================================================
RCS file: /cvs/Twisted/twisted/enterprise/row.py,v
retrieving revision 1.19
diff -u -r1.19 row.py
--- twisted/enterprise/row.py	4 Oct 2002 23:38:47 -0000	1.19
+++ twisted/enterprise/row.py	27 Apr 2003 18:05:15 -0000
@@ -64,6 +64,7 @@
 
     populated = 0    # set on the class when the class is "populated" with SQL
     dirty = 0        # set on an instance then the instance is out-of-sync with the database
+    case_sensitive_relations = 0    # set if you want relations (table / column names_ to be treated as case sensitive
 
     def assignKeyAttr(self, attrName, value):
         """Assign to a key attribute.
@@ -83,7 +84,7 @@
         """Find an attribute by caseless name.
         """
         for attr, type in self.rowColumns:
-            if string.lower(attr) == string.lower(attrName):
+            if self.compareRelations(attr,attrName):
                 return getattr(self, attr)
         raise DBError("Unable to find attribute %s" % attrName)
 
@@ -110,7 +111,7 @@
             if getKeyColumn(self.__class__, attr):
                 continue
             for column, ctype, typeid in self.dbColumns:
-                if string.lower(column) == string.lower(attr):
+                if self.compareRelations(column, attr):
                     q = dbTypeMap.get(ctype, None)
                     if q == NOQUOTE:
                         setattr(self, attr, 0)
@@ -131,6 +132,18 @@
         for keyName, keyType in self.rowKeyColumns:
             keys.append( getattr(self, keyName) )
         return tuple(keys)
+
+    def compareRelations(self, relation, attr):
+        """Wrap comparisons involving relations
+        
+        This allows for case-sensitive or case-insensitive comparisons
+        involving relations (table or column names), based on the value of
+        case_sensitive_relations.
+        """
+        if self.case_sensitive_relations:
+            return relation == attr
+        else:
+            return string.lower(relation) == string.lower(attr)
         
 
 class KeyFactory:
Index: twisted/enterprise/sqlreflector.py
===================================================================
RCS file: /cvs/Twisted/twisted/enterprise/sqlreflector.py,v
retrieving revision 1.14
diff -u -r1.14 sqlreflector.py
--- twisted/enterprise/sqlreflector.py	12 Jan 2003 06:26:48 -0000	1.14
+++ twisted/enterprise/sqlreflector.py	27 Apr 2003 18:05:16 -0000
@@ -17,7 +17,7 @@
 import string
 
 from twisted.enterprise import adbapi
-from twisted.enterprise.util import DBError, getKeyColumn, quote, _TableInfo, _TableRelationship
+from twisted.enterprise.util import DBError, getKeyColumn, quote_value, quote_relation, _TableInfo, _TableRelationship
 from twisted.enterprise.row import RowObject
 
 from twisted.enterprise import reflector
@@ -37,11 +37,14 @@
         reflector.GREATERTHAN : ">",
         reflector.LIKE        : "like"
         }
-    
-    def __init__(self, dbpool, rowClasses):
+    quote_relations = 0
+
+    def __init__(self, dbpool, rowClasses, **kw):
         """
         Initialize me against a database.
         """
+        if 'quote_relations' in kw:
+            self.quote_relations = kw['quote_relations']
         adbapi.Augmentation.__init__(self, dbpool)
         reflector.Reflector.__init__(self, rowClasses)        
 
@@ -87,7 +90,16 @@
         @param value: a value to format as data in SQL.
         @param type: a key in util.dbTypeMap.
         """
-        return quote(value, type, string_escaper=self.escape_string)
+        return quote_value(value, type, string_escaper = self.escape_string)
+    
+    def quote_relation(self, relation):
+        """Format a relation for use in a SQL statement.
+
+        @param relation: a string to format as a relation for SQL
+        examples of relations are table / column names.  For some
+        databases, they must be double quoted
+        """
+        return quote_relation(relation, self.quote_relations)
 
     def loadObjectsFrom(self, tableName, parentRow=None, data=None, whereClause=None, forceChildren=0):
         """Load a set of RowObjects from a database.
@@ -138,8 +150,8 @@
                 first = 0
             else:
                 sql = sql + ","
-            sql = sql + " %s" % column
-        sql = sql + " FROM %s " % (tableName)
+            sql = sql + " %s" % self.quote_relation(column)
+        sql = sql + " FROM %s " % self.quote_relation(tableName)
         if whereClause:
             sql += " WHERE "
             first = 1
@@ -151,7 +163,8 @@
                 (columnName, cond, value) = wItem
                 t = self.findTypeFor(tableName, columnName)
                 quotedValue = self.quote_value(value, t)
-                sql += "%s %s %s" % (columnName, self.conditionalLabels[cond], quotedValue)
+                quotedColumn = self.quote_relation(columnName)
+                sql += "%s %s %s" % (quotedColumn, self.conditionalLabels[cond], quotedValue)
 
         # execute the query
         transaction.execute(sql)
@@ -204,7 +217,7 @@
 
         Returns: SQL that is used to contruct a rowObject class.
         """
-        sql = "UPDATE %s SET" % tableInfo.rowTableName
+        sql = "UPDATE %s SET" % self.quote_relation(tableInfo.rowTableName)
         # build update attributes
         first = 1
         for column, type in tableInfo.rowColumns:
@@ -212,7 +225,7 @@
                 continue
             if not first:
                 sql = sql + ", "
-            sql = sql + " %s = %s" % (column, "%s")
+            sql = sql + " %s = %s" % (self.quote_relation(column), "%s")
             first = 0
 
         # build where clause
@@ -231,13 +244,13 @@
         Returns: SQL that is used to insert a new row for a rowObject
         instance not created from the database.
         """
-        sql = "INSERT INTO %s (" % tableInfo.rowTableName
+        sql = "INSERT INTO %s (" % self.quote_relation(tableInfo.rowTableName)
         # build column list
         first = 1
         for column, type in tableInfo.rowColumns:
             if not first:
                 sql = sql + ", "
-            sql = sql + column
+            sql = sql + self.quote_relation(column)
             first = 0
 
         sql = sql + " ) VALUES ("
@@ -256,23 +269,22 @@
     def buildDeleteSQL(self, tableInfo):
         """Build the SQL to delete a row from the table.
         """
-        sql = "DELETE FROM %s " % tableInfo.rowTableName
+        sql = "DELETE FROM %s " % self.quote_relation(tableInfo.rowTableName)
         # build where clause
         first = 1
         sql = sql + " WHERE "
         for keyColumn, type in tableInfo.rowKeyColumns:
             if not first:
                 sql = sql + " AND "
-            sql = sql + " %s = %s " % (keyColumn, "%s")
+            sql = sql + " %s = %s " % (self.quote_relation(keyColumn), "%s")
             first = 0
         return sql
 
-
     def updateRowSQL(self, rowObject):
         """build SQL to update my current state.
         """
         args = []
-        tableInfo = self.schema[rowObject.rowTableName]
+        tableInfo = self.schema[rowObject.rowTableName]        
         # build update attributes
         for column, type in tableInfo.rowColumns:
             if not getKeyColumn(rowObject.__class__, column):
@@ -313,11 +325,10 @@
         """build SQL to delete me from the db.
         """
         args = []
-        tableInfo = self.schema[rowObject.rowTableName]        
+        tableInfo = self.schema[rowObject.rowTableName]
         # build where clause
         for keyColumn, type in tableInfo.rowKeyColumns:
             args.append(self.quote_value(rowObject.findAttribute(keyColumn), type))
-
         return self.getTableInfo(rowObject).deleteSQL % tuple(args)
 
     def deleteRow(self, rowObject):
Index: twisted/enterprise/util.py
===================================================================
RCS file: /cvs/Twisted/twisted/enterprise/util.py,v
retrieving revision 1.12
diff -u -r1.12 util.py
--- twisted/enterprise/util.py	29 Jan 2003 04:51:19 -0000	1.12
+++ twisted/enterprise/util.py	27 Apr 2003 18:05:16 -0000
@@ -54,7 +54,7 @@
             return name
     return None
 
-def quote(value, typeCode, string_escaper=adbapi.safe):
+def quote_value(value, typeCode, string_escaper=adbapi.safe):
     """Add quotes for text types and no quotes for integer types.
     NOTE: uses Postgresql type codes..
     """
@@ -74,6 +74,18 @@
         if type(value) is not types.StringType:
             value = str(value)
         return "'%s'" % string_escaper(value)
+
+def quote_relation(relation, take_action=0):
+    """Format a relation for use in a SQL statement.
+
+    @param relation: a string to format as a relation for SQL
+    examples of relations are table / column names.  For some
+    databases, they must be double quoted
+    """
+    if take_action:
+        return '"%s"' % relation
+    else:
+        return str(relation)
 
 def makeKW(rowClass, args):
     """Utility method to construct a dictionary for the attributes
