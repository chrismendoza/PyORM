import copy
import operator
import warnings

from pyorm.exceptions import FieldsUndefinedError, DeclarationIndexMissingError, InvalidDefaultError
from pyorm.field import Field
from pyorm.index import Index, UniqueIndex
from pyorm.relationship import Relationship

class MetaModel(type):
    """
        MetaModel is the metaclass for creating new model classes, inserting missing optional
        sections, as well as recording all unique keys, the names of all the field, relationship
        and index attributes (in their declared order), so that later lookups can be done on via
        a tuple lookup, rather than doing a getattr(Model.Field, attr_name) each time.

        This class also records the unique fields as defined by primary/unique indexes so that we
        can quickly reference those as well.

        If no unique index/primary key is defined on the model, a warning is thrown, as it could
        cause some major issues later when updating or deleting a record through the model.

        This class is also responsible for assigning the table name (if it was not declared).
    """

    _cache = {}

    def __new__(cls, name, bases, attrs):
        """
            Set up the new instance of the Model subclass, making sure that all parts are there
        """
        # We don't want to modify the Model class itself, only its subclasses
        if not len(set(base for base in bases if isinstance(base, MetaModel))):
            return type.__new__(cls, name, bases, attrs)

        if name in cls._cache.keys():
            return cls._cache[name]

        # Define a new instance of this class
        new_class = type.__new__(cls, name, bases, attrs)

        # temporary container for the unique field names that apply to this model
        unique_fields = []

        field_list = []
        # the ORM requires fields to be defined, throw an error if they're not
        try:
            field_objects = cls.sorted_object_matches(new_class.Fields, Field)
            if len(field_objects) == 0:
                raise FieldsUndefinedError(name)
        except:
            raise FieldsUndefinedError(name)

        # process the field_objects, looking for primary key fields
        for field_name, field, dindex in field_objects:
            # raise an error here if we encounter a model field that has a default of null (None in python) and
            # does not allow nulls.  The only exception to this rule is autoincrement fields.
            if not field.null and field.default is None and not field.autoincrement:
                #raise InvalidDefaultError(name, field_name, 'Field set to not allow nulls, but null specified as the default value')
                warnings.warn('Field `{0}`.`{1}` is set to not allow nulls, but has a default value of None (null).'.format(name, field_name))
            field.name = field_name
            field_list.append(field_name)
            if field.primary_key:
                unique_fields.append(field_name)

        new_class.Fields._field_list = tuple(field_list)

        # Loop through the allowable types
        for optional_class in {'Relationships','Indexes','Meta'}:
            if not getattr(new_class, optional_class, False):
                # fill in the optional classes that are missing to prevent references to 
                # objects that dont exist, as well as having to check for the object
                setattr(new_class, optional_class, type(optional_class, (object,), {})())

            if optional_class == 'Relationships':
                relationship_list = []
                relationship_objects = cls.sorted_object_matches(new_class.Relationships, Relationship)

                for relationship_name, relationship, dindex in relationship_objects:
                    relationship_list.append(relationship_name)

                new_class.Relationships._relationship_list = tuple(relationship_list)
                new_class.Relationships._thin_relationship_list = []

            elif optional_class == 'Indexes':
                index_list = []
                index_objects = cls.sorted_object_matches(new_class.Indexes, Index)

                for index_name, index, dindex in index_objects:
                    index_list.append(index_name)
                    if type(index) is UniqueIndex:
                        unique_fields.extend(index._fields)

                new_class.Indexes._index_list = tuple(index_list)
                new_class.Indexes._unique_columns = tuple(unique_fields)

        if not len(unique_fields):
            #warnings.warn("Model `{0}` has no unique indexes or primary key defined, this could cause undesired results when updating/deleting records.".format(name))
            pass

        # If the table attribute of the Meta object is not defined, define it as the model name
        if not getattr(new_class.Meta, u'table', False):
            new_class.Meta.table = name

        # set the model alias (this is normally the name of the model, 
        # but in the case of relations this is the relationship name, 
        # which is set by the parent)
        new_class.Meta.table_alias = name

        cls._cache[name] = new_class
        return new_class

    @classmethod
    def sorted_object_matches(cls, obj, sub_type):
        """
            Returns a list of subobjects, given an object to iterate through and a class type to
            look for within the objects attributes.  This function expects that any type passed
            to this class will contain the declaration_index attribute, which reflects the order
            in which that class attribute was initialized.  Doing this allows us to maintain the
            ordering for those attributes in the way the user originally intended.

            This is especially useful when creating a table in the database, where it is important
            to preserve the ordering of columns and indexes (especially in the case of merge tbls).
        """
        try:
            sub_objects = ((o[0], o[1], o[1].declaration_index) for o in obj.__dict__.items() if issubclass(type(o[1]), sub_type))
        except AttributeError:
            raise DeclarationIndexMissingError(sub_type)

        return sorted(sub_objects, key=operator.itemgetter(2))

