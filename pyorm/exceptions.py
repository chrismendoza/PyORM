class FieldsUndefinedError(Exception):
    def __init__(self, name):
        Exception.__init__(self, u'The model \'{0}\' has no fields defined, please define them before attempting to use the model.'.format(name))


class FieldError(Exception):
    def __init__(self, name):
        Exception.__init__(self, u"The field name '{0}' has already been taken, and cannot be reused.".format(name))


class IntegerConversionError(Exception):
    def __init__(self, name, value_type):
        Exception.__init__(self, u'The field `{0}` expected an integer value, got type `{1}`.'.format(name, value_type))


class DatabaseColumnTypeMismatchError(Exception):
    def __init__(self, name, expected_type, value_type):
        Exception.__init__(self, u'The field `{0}` expected type `{1}` from the database, got type `{2}`.'.format(name, expected_type, value_type))


class UnionArgumentTypeError(Exception):
    def __init__(self):
        Exception.__init__(
            self, u'Unions expect arguments that are subclasses of Model.')


class UnionColumnTypeError(Exception):
    def __init__(self):
        Exception.__init__(self, u'Unions cannot use standard fields, define custom fields when using Unions.')


class UnionColumnDefinitionError(Exception):
    def __init__(self):
        Exception.__init__(self, u'Models assigned to unions must contain all the same fields.')


class ColumnNotInResultError(Exception):
    def __init__(self, name, model_name):
        Exception.__init__(self, u'Column or Alias `{0}` was not selected to be pulled back with the current result set for model `{1}`.'.format(name, model_name))


class RelationshipsImmutableError(Exception):
    def __init__(self, name, model_name):
        Exception.__init__(self, u'The relationship `{0}` on model `{1}` cannot be overwritten by another value'.format(name, model_name))


class RelationshipChainError(Exception):
    def __init__(self, column_chain, model_name):
        Exception.__init__(self, u'Relationship chain `{0}` does not exist for model `{1}`.'.format(column_chain, model_name))


class RelationshipLoadError(Exception):
    def __init__(self):
        Exception.__init__(self, u'Cannot add a field from a on to many or many to many relationship, doing so could result in multiple copies of the same row for this model.')


class DynamicThinModelCreationError(Exception):
    def __init__(self, relationship):
        Exception.__init__(self, u'Could not dynamically add ThinRelationship/ThinModel `{0}`, no definition available.'.format(relationship))


class MultiRowInsertDataError(Exception):
    def __init__(self, data_type):
        Exception.__init__(self, u'For a multi-row insert, each row is expected to be a dict, got `{0}`.'.format(data_type))


class RecordNotLoadedError(Exception):
    def __init__(self):
        Exception.__init__(
            self, u'Tried to update/delete a model with no record loaded.')


class NullAssignmentError(Exception):
    def __init__(self, column_name):
        Exception.__init__(self, u'Tried to assign None to `{0}`, which does not allow nulls.'.format(column_name))


class InvalidDefaultError(Exception):
    def __init__(self, model_name, column_name, reason):
        Exception.__init__(self, u'Invalid default specified for `{0}.{1}`, reason: {2}.'.format(model_name, column_name, reason))


class DeclarationIndexMissingError(Exception):
    def __init__(self, obj_type):
        Exception.__init__(self, u'Object type `{0}` is missing declaration_index'.format(obj_type.__class__.__name__))
