from pyorm.connection import exceptions
from pyorm.expression import Expression
from pyorm.field import Field
from pyorm.index import Index, UniqueIndex, FullTextIndex, SpatialIndex
from pyorm.relationship import ThinRelationship
from pyorm.relationship import Relationship

import copy
import MySQLdb
import re
import traceback



class mysqlConnection(object):
    @property
    def dialect(self):
        return mysqlDialect()

    def __init__(self, **kwargs):
        """
            Initialize the connection
        """
        config = copy.copy(kwargs)
        self._debug = config.pop('debug', False)
        self._autocommit = config.pop('autocommit', False)
        self._post_connect = config.pop('post_connect', [])
        self._database = config.pop('db', False)
        self._auto_create_tables = config.pop('auto_create_tables', False)
        self._auto_create_columns = config.pop('auto_create_columns', False)

        del config['dialect']

        self._connection = MySQLdb.connect(**config)

        if self._database:
            self.select_db(self._database)
        if self._autocommit:
            self.query('SET autocommit=1')
        if self._post_connect:
            self.post_connect()

    def __del__(self):
        """
            Close this connection when deleting the object
        """
        self.close()

    def query(self, sql, values=[]):
        """
            Query method, relies on the query, values and engine (if defined)
        """
        retval = {}
        if self.test():
            if self._debug:
                self._debug_object = {
                    'host': self._connection.get_host_info(),
                    'port': self._connection.port,
                    'errno': None,
                    'errstr': None,
                    'traceback': None,
                    'result_set': False,
                    'count': 0,
                    'insert_id': None
                }

            cursor = self._connection.cursor(MySQLdb.cursors.DictCursor)
            try:
                cursor.execute(sql, values)
                retval = {
                    'result_set': cursor.fetchall(),
                    'count': cursor.rowcount,
                    'insert_id': self._connection.insert_id()
                }
                if self._debug:
                    retval['debug_object'] = self._debug_object

            except MySQLdb.ProgrammingError as (errno, errstr):
                if self._debug:
                    self._debug_object['errno'] = errno
                    self._debug_object['errstr'] = errstr
                    self._debug_object['traceback'] = traceback.format_exc()

                if errno == 1146:
                    raise exceptions.TableMissingError([match.groups()[0].split('.')[-1] for match in re.finditer('\'(.*?)\'', errstr)])
                else:
                    raise

            except MySQLdb.OperationalError as (errno, errstr):
                if self._debug:
                    self._debug_object['errno'] = errno
                    self._debug_object['errstr'] = errstr
                    self._debug_object['traceback'] = traceback.format_exc()

                if errno == 1054:
                    raise exceptions.ColumnMissingError
                else:
                    raise

            except Exception as error:
                if self._debug:
                    self._debug_object['errno'] = ''
                    self._debug_object['errstr'] = error
                    self._debug_object['traceback'] = traceback.format_exc()
                raise
            finally:
                if self._debug:
                    self._debug_object['sql'] = cursor._last_executed

        if self._debug:
            retval['debug_object'] = self._debug_object

        return retval

    def literal(self, values):
        return self._connection.literal(values)

    def select_db(self, database):
        """ change to/select a given database """
        self._database = database
        return self._connection.select_db(database)

    def create_db(self, database):
        """ Create the specified database, automatically does an if not exists """
        return self.query('CREATE DATABASE IF NOT EXISTS `{0}`'.format(database))

    def delete_db(self, database):
        return self.query('DROP DATABASE IF EXISTS `{0}`'.format(database))

    def create_table(self, model):
        """ Create the model passed on this database connection """
        try:
            return self.query(*self.dialect.create_table(model))
        except Exception as error:
            raise exceptions.TableCreationError(model.Meta.table, error)

    def test(self):
        """ A polling method to see if the connection is still active """
        if self._connection.open:
            return True
        else:
            return False

    def start_transaction(self):
        """
            Method to start a transaction
        """
        if self._connection.query('START TRANSACTION'):
            return True
        return False

    def rollback(self):
        """
            Rollback the current transaction
        """
        if self._connection.query('ROLLBACK'):
            return True
        return False

    def commit(self):
        """
            Commit the current transaction
        """
        if self._connection.query('COMMIT'):
            return True
        return False

    def close(self):
        """ Close this connection """
        if getattr(self, '_connection', False) and self._connection.open:
            self._connection.close()

    def post_connect(self):
        if len(self._post_connect):
            for instruction in self._post_connect:
                self.query(instruction)


class mysqlDialect(object):
    """
        Class for parsing the dialect for the MySQL connections
    """
    operators = {
        'ADD': '+',
        'SUB': '-',
        'DIV': '/',
        'MUL': '*',
        'MOD': '%%',
        'EQ': '=',
        'NULLEQ': 'IS',
        'NE': '!=',
        'NULLNE': 'IS NOT',
        'GT': '>',
        'LT': '<',
        'GE': '>=',
        'LE': '<=',
        'LPARENTHESIS': '(',
        'RPARENTHESIS': ')',
        'BITWISE_AND': '&',
        'BITWISE_OR': '|',
    }

    fields = {}

    keywords = {
        'GROUPCONCAT': 'GROUP_CONCAT',
        'ORDER': 'ORDER BY',
        'AVERAGE': 'AVG',
        'MINIMUM': 'MIN',
        'MAXIMUM': 'MAX',
        'ASCENDING': 'ASC',
        'DESCENDING': 'DESC',
        'CURRENTTIMESTAMP': 'CURRENT_TIMESTAMP',
        'BOOLEANMODE': 'IN BOOLEAN MODE',
        'NATURALLANG': 'IN NATURAL LANGUAGE MODE',
        'QUERYEXPAND': 'WITH QUERY EXPANSION'
    }

    def translate(self, token_stream, ref_model=False):
        from pyorm.token import Token

        translated = []
        values = []
        for index, token in enumerate(token_stream):
            if token[0] is Token.Operator:
                op = token[1]
                if op in (',', 'RPARENTHESIS'):
                    translated.append('{0} '.format(self.operators.get(op, op)))
                elif token[1] == 'LPARENTHESIS':
                    translated.append(self.operators.get(op, op))
                elif op == 'EQ' and type(token_stream[index + 1][1]) in (tuple, list) or token_stream[index + 1][0] == Token.Model:
                    op = 'IN'
                    translated.append(' {0} '.format(self.operators.get(op, op)))
                elif op == 'NE' and type(token_stream[index + 1][1]) in (tuple, list) or token_stream[index + 1][0] == Token.Model:
                    op = 'NOT IN'
                    translated.append(' {0} '.format(self.operators.get(op, op)))
                elif op == 'CONTAINS':
                    op = 'LIKE'
                    translated.append(' {0} '.format(self.operators.get(op, op)))
                    token_stream[index + 1] = (Token.Literal, '%{0}%'.format(token_stream[index + 1][1]))
                elif op == 'STARTSWITH':
                    op = 'LIKE'
                    translated.append(' {0} '.format(self.operators.get(op, op)))
                    token_stream[index + 1] = (Token.Literal, '{0}%'.format(token_stream[index + 1][1]))
                elif op == 'ENDSWITH':
                    op = 'LIKE'
                    translated.append(' {0} '.format(self.operators.get(op, op)))
                    token_stream[index + 1] = (Token.Literal, '%{0}'.format(token_stream[index + 1][1]))
                else:
                    translated.append(' {0} '.format(self.operators.get(token[1], token[1])))
            elif token[0] is Token.Literal:
                if type(token[1]) in (tuple, list):
                    translated.append('({0})'.format(','.join(['%s'] * len(token[1]))))
                    values.extend(token[1])
                else:
                    translated.append('%s')
                    values.append(token[1])
            elif token[0] is Token.Alias:
                translated.append(' AS `{0}`'.format(token[1]))
            elif token[0] is Token.Column:
                translated.append(self.format_column(token[1], ref_model=ref_model))
            elif token[0] is Token.Keyword:
                if token[1].upper() not in ('UNION', 'ORDER', 'SEPARATOR'):
                    translated.append(' {0}'.format(self.keywords.get(token[1].upper(), token[1].upper())))
                else:
                    translated.append(' {0} '.format(self.keywords.get(token[1].upper(), token[1].upper())))
            elif token[0] is Token.Model:
                try:
                    token[1]._properties.subquery_parent = self._model
                    token[1]._properties.subquery = True
                except AttributeError:
                    pass

                if token[1]._properties.wrap:
                    translated.append('({0})'.format(token[1].get(False)))
                else:
                    translated.append('{0}'.format(token[1].get(False)))
                values.extend(token[1]._properties.escaped_values)
        return u''.join(translated), values

    def create_table(self, model):
        fields, literals = self.format_fields(model)
        sql = "CREATE TABLE IF NOT EXISTS {0} ({1})".format(self.format_table(model, False), ','.join((fields, self.format_indexes(model))))
        sql += ' ENGINE={0}'.format(getattr(model.Meta, 'engine', 'MYISAM'))

        if getattr(model.Meta, 'charset', False):
            sql += ' DEFAULT CHARSET {0}'.format(model.Meta.charset)

        return sql, literals

    def format_fields(self, model):
        fields = []
        literals = []
        for name in model.Fields._field_list:
            field = getattr(model.Fields, name)
            try:
                field_def, field_def_literals = self.translate(field.tokenize())
            except AttributeError:
                field_def, field_def_literals = (self.fields.get(field.field_type, field.field_type), [])

            sql = '`{0}` {1}'.format(name, field_def)
            literals.extend(field_def_literals)

            if getattr(field, 'precision', False):
                sql += '(%s, %s)'
                literals.extend((field.precision, field.scale))
            elif getattr(field, 'length', False):
                sql += '(%s)'
                literals.append(field.length)

            if getattr(field, 'unsigned', False):
                sql += ' UNSIGNED'

            if not getattr(field, 'null', False):
                sql += ' NOT NULL'

            if getattr(field, 'autoincrement', False):
                sql += ' AUTO_INCREMENT'
            elif getattr(field, 'default', False) is not False:
                try:
                    default, default_literals = self.translate(field.default.tokenize())
                    sql += ' DEFAULT {0}'.format(default)
                    literals.extend(default_literals)
                except AttributeError:
                    sql += ' DEFAULT %s'
                    literals.append(field.default)

            fields.append(sql)

        return ', '.join(fields), literals

    def format_indexes(self, model):
        indexes = []
        literals = []

        primary_key_fields = []
        for name in model.Fields._field_list:
            field = getattr(model.Fields, name)
            if field.primary_key or field.autoincrement:
                primary_key_fields.append(name)

        if len(primary_key_fields):
            indexes.append(" PRIMARY KEY ({0})".format(', '.join('`{0}`'.format(field) for field in primary_key_fields)))

        for name in model.Indexes._index_list:
            index = getattr(model.Indexes, name)
            if issubclass(type(index), UniqueIndex):
                indexes.append(" UNIQUE INDEX `{0}` ({1})".format(name, ', '.join('`{0}`'.format(field) for field in index._fields)))
            elif issubclass(type(index), FullTextIndex):
                indexes.append(" FULLTEXT INDEX `{0}` ({1})".format(name, ', '.join('`{0}`'.format(field) for field in index._fields)))
            elif issubclass(type(index), SpatialIndex):
                indexes.append(" SPATIAL INDEX `{0}` ({1})".format(name, ', '.join('`{0}`'.format(field) for field in index._fields)))
            else:
                indexes.append(" INDEX `{0}` ({1})".format(name, ', '.join('`{0}`'.format(field) for field in index._fields)))

        return ', '.join(indexes)


    def select(self, model):
        """
            Formats a select statement from the model passed,
            returns the raw sql and the values that need to be
            substituted into the query by the mysql connection
        """
        self._model = model
        literals = []

        # Merge the standard (column) fields and the
        # User defined fields into one expression group
        fields = Expression().operator(',')
        fields.extend(model._standard_fields)
        fields.extend(model._additional_fields)

        # Add the escaped values from the fields to the value set
        trans, values = self.translate(fields.tokenize())
        sql = u'SELECT {0} FROM {1}'.format(trans, self.format_table(model))
        literals.extend(values)

        if len(model._eager_load):
            joins, values = self.format_joins(model)
            sql += joins
            literals.extend(values)

        if len(model._filter):
            trans, values = self.translate(model._filter.tokenize())
            sql += u' WHERE {0}'.format(trans)
            literals.extend(values)

        if len(model._group):
            trans, values = self.translate(model._group.tokenize())
            sql += u' GROUP BY {0}'.format(trans)
            literals.extend(values)

        if len(model._having):
            trans, values = self.translate(model._having.tokenize())
            sql += u' HAVING {0}'.format(trans)
            literals.extend(model._having.escaped_values())

        if len(model._order):
            trans, values = self.translate(model._order.tokenize())
            sql += u' ORDER BY {0}'.format(trans)
            literals.extend(values)

        if model._limit is not None:
            sql += u' LIMIT %s, %s'
            literals.extend(model._limit)

        return sql, literals

    def insert(self, model):
        """
            Formats an insert statement from the model passed,
            returns the raw sql and the values that need to be
            substituted into the query by the mysql connection
        """
        self._model = model
        from pyorm.token import Token
        literals = []
        tokens = model._standard_fields.tokenize()

        trans, values = self.translate(tokens)
        literals.extend(values)

        if len(filter(lambda x: x[0] is Token.Keyword and x[1] == 'Values', tokens)):
            sql = u'INSERT INTO {0} {1}'.format(self.format_table(model, False), trans)
        else:
            sql = u'INSERT INTO {0} SET {1}'.format(self.format_table(model, False), trans)

        return sql, literals

    def update(self, model):
        """
            Formats an update statement from the model passed,
            returns the raw sql and the values that need to be
            substituted into the query by the mysql connection
        """
        self._model = model
        literals = []
        trans, values = self.translate(model._standard_fields.tokenize())
        literals.extend(values)
        sql = u'UPDATE {0} SET {1}'.format(self.format_table(model, False), trans)

        if len(model._filter):
            trans, values = self.translate(model._filter.tokenize())
            sql += u' WHERE {0}'.format(trans)
            literals.extend(values)

        return sql, literals

    def delete(self, model):
        """
            Formats a delete statement from the model passed,
            returns the raw sql and the values that need to be
            substituted into the query by the mysql connection
        """
        self._model = model
        literals = []
        sql = u'DELETE FROM {0}'.format(self.format_table(model, False))

        if len(model._filter):
            trans, values = self.translate(model._filter.tokenize())
            sql += u' WHERE {0}'.format(trans)
            literals.extend(values)

        return sql, literals

    def replace(self, model):
        """
            Formats a replace statement from the model passed,
            returns the raw sql and the values that need to be
            substituted into the query by the mysql connection
        """
        self._model = model
        from pyorm.token import Token
        literals = []
        tokens = model._standard_fields.tokenize()

        trans, values = self.translate(tokens)
        literals.extend(values)

        if len(filter(lambda x: x[0] is Token.Keyword and x[1] == 'Values', tokens)):
            sql = u'REPLACE INTO {0} {1}'.format(self.format_table(model, False), trans)
        else:
            sql = u'REPLACE INTO {0} SET {1}'.format(self.format_table(model, False), trans)

        return sql, literals

    def format_table(self, model, include_alias=True):
        chain = []
        if model._properties.subquery:
            chain.append(['subquery', 'subquery', ''])

        tables = []
        chain.extend(model._properties.tree)
        if include_alias:
            table_string = '`{0}` AS `{1}`'.format(
                model._properties.tree[-1][1],
                u'.'.join(model[0] for model in chain)
            )
        else:
            table_string = '`{0}`'.format(
                model._properties.tree[-1][1],
            )
        tables.append(table_string)

        if getattr(model, 'Relationships', None) and include_alias:
            for relationship_name, rel in model.Relationships.__dict__.items():
                if issubclass(type(rel), ThinRelationship):
                    chain = []

                    if model._properties.subquery:
                        chain.append(['subquery', 'subquery', ''])

                    chain.extend(rel.model._properties.tree)

                    if include_alias:
                        table_string = '`{0}` AS `{1}`'.format(
                            rel.model._properties.tree[-1][1],
                            u'.'.join(model[0] for model in chain)
                        )
                    else:
                        table_string = '`{0}`'.format(
                            rel.model._properties.tree[-1][1],
                        )
                    tables.append(table_string)

        return u','.join(tables)

    def format_joins(self, model, load_list=False, include_alias=True):
        joins = []
        escaped_values = []
        if load_list is False:
            load_list = model._eager_load

        if len(load_list):
            for rel in load_list.keys():
                current_relation = getattr(model.Relationships, rel)
                if type(current_relation) is not ThinRelationship:
                    conditions, values = self.translate(current_relation.conditions.tokenize(), ref_model=model)
                    joins.append(' {0} JOIN {1} ON {2}'.format(
                        current_relation._join,
                        self.format_table(current_relation.model),
                        conditions
                    ))
                    escaped_values.extend(values)

                    if len(load_list[rel]):
                        vals = self.format_joins(getattr(model.Relationships, rel)._model, load_list[rel])
                        joins.append(vals[0])
                        escaped_values.extend(vals[1])

        return (' '.join(joins), escaped_values)

    def format_column(self, column, ref_model=False):
        """
            Format the column object in the form:
                [subquery.]basemodel.[related_model.]field
        """
        column_base = []
        try:
            mode = self._model._properties.mode

            if self._model._properties.subquery and not column._scope:
                column_base.append('subquery')

            if column._scope:
                base = self._model._properties.subquery_parent
            else:
                if ref_model is not False:
                    base = ref_model
                else:
                    base = self._model

            try:
                for mod in column._queue[:-1]:
                    base = getattr(base.Relationships, mod).model

                field_def = column._queue[-1] in base.Fields._field_list
            except:
                field_def = False

            if mode == 'write':
                col = u'`{0}`'.format(column._queue[-1])
            elif not field_def:
                col = u'`{0}`'.format(u'.'.join(column._queue))
            else:
                if (self._model._properties.subquery and not column._scope) or not self._model._properties.subquery:
                    if ref_model is not False:
                        column_base.extend(ref_model._properties.column_chain)
                    else:
                        column_base.extend(self._model._properties.column_chain)
                elif column._scope:
                    # process subquery field that is set to the parent scope
                    column_base.extend(self._model._properties.subquery_parent._properties.column_chain)

                column_base.extend(column._queue)
                col = u'`{0}`.`{1}`'.format(u'.'.join(column_base[:-1]), column_base[-1])

                if column._alias is not None and mode == 'read':
                    col = u'{0} AS `{1}`'.format(col, u'.'.join(column_base))

            return col
        except AttributeError:
            return u'`{0}`'.format(u'.'.join(column._queue))

