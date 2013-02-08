PyORM
=====

# Configuration
# Building a model with PyORM
## Fields
## Relationships
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
```
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.filter(C.field1 == 'test')
m.scalar()
```
`Model.scalar()` - Returns the first value from the first matching row in the database.
```
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.filter(C.field1 == 'test')
m.one()
```
`Model.one()` - Returns the first matching row from the database.
```
from pyorm import Column as C
from examples import SampleModel


m = SampleModel()
m.filter(C.field1 == 'test')
m.get()
```
`Model.get()` - Returns all rows which match the filters specified.
```
from examples import SampleModel


m = SampleModel()
m.all()
```
`Model.all()` - Returns all rows that belong to this model, ignores any filters set on the model.

```
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
# Advanced Concepts
## Helpers
## Subqueries
## Mapping objects
## Adding fields and relationships after instantiation
## Temporary Tables