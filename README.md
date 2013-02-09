PyORM
=====

# Configuration
# Building a model with PyORM
Models in PyORM act as a direct representation of a table object in your chosen database, but also perform some other important functions, such as:
* Keeping track of which fields and compound fields have been requested.
* Tracking which filters you want to apply to a given select/update/delete/replace operation.
* Tracking how you want to group the data that comes back from `SELECT` queries.
* Mapping returned data to a mapping object you provide instead of returning a model to iterate over.

The simplest model definition you could possibly create with PyORM is:
```python
from pyorm import Model


class SimpleModel(Model):
    pass
```
Though this model doesn't do much of anything, it will set up a few things behind the scenes, including an integer column called `id`, which is autoincrementing, unsigned, and assigned as the primary key for this table.  It also automatically creates `SimpleModel.Meta` and `SimpleModel.Indexes` attributes, which are both used internally.  SimpleModel.Meta is also used for various settings which you can manipulate at runtime (more on that in the Meta data section).

The reason PyORM creates the `SimpleModel.id` column is that it helps ensure that some sort of index is attached to each table, even if you choose not to define one.  This should help related queries run more quickly when you create simple relationships.  For instructions on how to turn this behaviour off, see the Meta data section (this would be especially important in cases where you have a pre-existing database schema).
## Fields
For pretty much every model you create, the above example will not be enough, you will also need to have columns to store your data on.  PyORM has quite a few field types out of the box, with the simplest being `Integer`, `Char`, `Decimal`, `Date`, and `Time`.

```python
from pyorm import Model, Integer


class SampleModel(Model):
    field1 = Integer(length=8, unsigned=True, default=0, null=False)
```

Fields are defined on the main Model class, but because there are several methods defined on the Model class, you may run into situations where your table name conflicts with one of those methods.  If you do run into this situation, PyORM allows you to suffix your field name with `_`, and the trailing `_` will automatically be stripped when pushing data to the database, as well as when the model is created (if you are using PyORM to create your database schema).
```python
from pyorm import Model, Integer


class SampleModel(Model):
    field1 = Integer(length=8, unsigned=True, default=0, null=False)
    conflicting_name_ = Integer(length=8, unsigned=True, default=0, null=False)
```
If for some reason after you instantiate `SampleModel`, you need to add another field, you can easily do so in the following way:
```python
m = SampleModel()
m.field2 = Char(length=255)
```
## Relationships
Relationships are the way in which PyORM connects one model to another, and relationships can be added in any of the following ways.
```python
from pyorm import Model, Integer, OneToMany
from examples import Sample3rdModel


class SampleModel(Model):
    field1 = Integer(length=8, unsigned=True, default=0, null=False)
    conflicting_name_ = Integer(length=8, unsigned=True, default=0, null=False)
    
    relationship1 = OneToMany(Sample3rdModel)
```
Builds a field called `relationship1_id` on the SampleModel table, and uses that field to map to `Sample2ndModel.id` (or whatever the primary key is).  This is the default behavior when no filters are defined on a relationship.
```python
from pyorm import Model, Integer, OneToMany
from examples import Sample3rdModel


class SampleModel(Model):
    field1 = Integer(length=8, unsigned=True, default=0, null=False)
    conflicting_name_ = Integer(length=8, unsigned=True, default=0, null=False) 
    
    relationship1 = OneToMany(Sample2ndModel)
    relationship2 = OneToMany(
        Sample3rdModel, filter=[C.field1 == C.relationship2.extra_id])
```
Uses the filters provided to gather the related `Sample2ndModel` results does not build an actual field on the model, so any mappings have to be done by hand. This should be used when dealing with a legacy database, or in the case that multiple fields are mapped across a pair of tables.
```python
from pyorm import Model, Integer
from examples import Sample3rdModel


class SampleModel(Model):
    field1 = Integer(length=8, unsigned=True, default=0, null=False)
    conflicting_name_ = Integer(length=8, unsigned=True, default=0, null=False) 
    
    relationship1 = OneToMany(
        'Sample2ndModel', import_from='path.to.model')
    relationship2 = OneToMany(
        Sample3rdModel, filter=[C.field1 == C.relationship2.extra_id])

```
Relationships can refer to models not in the current namespace as well by providing the name of the model as the first argument, and the import path via the import_from keyword arguement.  This is also useful when trying to avoid circular imports, and can be used with filters as well.  This type of relationship can be seen in `SampleModel.relationship1` above.

This method of importing can also be used to limit the models that are imported when the `SampleModel` is loaded, as importing SampleModel would cause `Sample2ndModel` to be imported, as well as any other models which are connected to `Sample2ndModel`.

```python
from pyorm import Model, Integer
from examples import Sample3rdModel, Sample4thModel, Sample6thModel


class SampleModel(Model):
    field1 = Integer(length=8, unsigned=True, default=0, null=False)
    conflicting_name_ = Integer(length=8, unsigned=True, default=0, null=False) 
    
    relationship1 = OneToMany(
        'Sample2ndModel', import_from='path.to.model')
    relationship2 = OneToMany(
        Sample3rdModel, filter=[C.field1 == C.relationship2.extra_id])

m = SampleModel()
# simple relationship added
m.relationship3 = OneToMany(Sample4thModel)

# simple non-circular relationship
m.relationship4 = OneToMany('Sample5thModel', import_from='path.to.model')

# relationship added with filters
m.relationship5 = OneToMany(
    Sample6thModel, filter=[C.field1 == C.relationship4.extra_id])
```
If you have a need to add a relationship for a specific query, the easiest and cleanest way to do it is to add the relationship directly to the Model instance you intend to pull data from.

```python
from pyorm import Model, Integer
from examples import Sample3rdModel, Sample4thModel, Sample6thModel


class SampleModel(Model):
    field1 = Integer(length=8, unsigned=True, default=0, null=False)
    conflicting_name_ = Integer(length=8, unsigned=True, default=0, null=False) 
    
    relationship1 = OneToMany(
        'Sample2ndModel', import_from='path.to.model')
    relationship2 = OneToMany(
        Sample3rdModel, filter=[C.field1 == C.relationship2.extra_id])

m = SampleModel()
m.r.relationship1.join = 'left'
```
By default, relationships in PyORM are assumed to be an inner join, where there must be a matching row in both the primary model and the model it is related to in order to pull back a record, however there are some occasions where you may want to pull back all records from the main model object, regardless of whether or not there is a matching related object.  In these cases, the relationships you defined can be tweaked by changing the `Relationship.join` attribute as seen above.  NOTE: All relationships can be accessed when dealing with a model via `Model.r.[relationship_name]`.
## Indexes
## Meta data
# Retrieving / Storing / Deleting Data
## Choosing Fields
By default, PyORM will pull back any and all fields for the base model, as well as any relationships which might be referenced in the filters, grouping, having, or ordering statements you specify.  In some cases however, it makes sense to trim down the data set returned by the database in order to reduce transmission and processing time needed in your application, especially when dealing with large data sets.

PyORM supports two types of fields, the first is a regular column selection, where you specify the fields you want from the model and any relationships it is attached to.  This can be achieved this way:
```python
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.fields(C.field1, C.rel1.field2)
m.get()
```
In the example above, we are selecting only `SampleModel.field1` and `SampleModel.rel1.field2`, however, it should be noted that in order to allow you to save data in the future, any PrimaryKey or UniqueKey fields that exist on the model and any relationships marked to also be loaded (in this case the fields from `SampleModel.rel1`) will be pulled back as well, so that an update can be performed if necessary.

PyORM also supports returning a SQL expression as a column using keyword arguments, as long as that column name does not conflict with any of the real field names on the model, or the methods that are native to the model class.

```python
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.fields(test_field=(C.field1 * C.rel1.field2))
m.get()
```
In the example above, `m.test_field` would now contain the product of `SampleModel.field1` and `SampleModel.rel1.field2` and would be accessable while iterating over or accessing each row of the model.  It should be noted that the expression evaluation is actually done on the database server you are using, so any output will be dependant on the technologies you choose to deploy.
## Filtering
## Grouping
## Ordering
## Selecting Data
PyORM offers four different options for retrieving data from your database:
```python
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.filter(C.field1 == 'test')
m.scalar()
```
`Model.scalar()` - Returns the first value from the first matching row in the database.
```python
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.filter(C.field1 == 'test')
m.one()
```
`Model.one()` - Returns the first matching row from the database.
```python
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.filter(C.field1 == 'test')
m.get()
```
`Model.get()` - Returns all rows which match the filters specified.
```python
from examples import SampleModel


m = SampleModel()
m.all()
```
`Model.all()` - Returns all rows that belong to this model, ignores any filters set on the model.
```python
from examples import SampleModel


m = SampleModel()
for row in m:
  # Do something with the data here
```
Alternatively you can choose to just iterate over the model you are working with, in which case `Model.get()` or `Model.all()` are called depending on whether or not you have defined filters on your model.
## Inserting Data
## Updating Data
## Deleting Data
## Replacing Data
# Advanced Concepts & Types
## Fields
## Helpers
## Subqueries
## Mapping objects
## Adding fields and relationships after instantiation
## Temporary Tables
