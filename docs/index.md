# Order of rules execution

| Rule         | jsonschema           | cerberus     | input  | output    |
|--------------|----------------------|--------------|--------|-----------|
| nullable     | type: null           | nullable     | o      | o -> pc   |
| type         | type                 | type         | o      |           |
| coerce       |                      | coerce       | o      | o         |
| regex        | pattern              | regex        | o      |           |
| format       | format               |              | o      |           |
| // o, orig   |                      |              | o      | orig      |
| schema       |                      |              | orig   | o         |
| map          |                      |              | o      | o         |
| enum         | enum                 | allowed      | o      |           |
| min          | minimum              | min          | o      |           |
| max          | maximum              | max          | o      |           |
| min_len      | minLength            | minlength    | o      |           |
| max_len      | maxLength            | maxlength    | o      |           |
|              | multipleOf           |              |        |           |
|              | exclusiveMinimum     |              |        |           |
|              | exclusiveMaximum     |              |        |           |
| min_len      | minItems             |              | o      |           |
| max_len      | maxItems             |              | o      |           |
|              | uniqueItems          |              |        |           |
|              | contains             | contains     |        |           |
| min_len      | minProperties        |              | o      |           |
| max_len      | maxProperties        |              | o      |           |
|              | allOf                | allof        |        |           |
| any_of       | anyOf                | anyof        | o      | o         |
| one_of       | oneOf                | oneof        | o      | o         |
|              |                      | noneof       |        |           |
|          pc: |                      |              |        |           |
| if_null      |                      |              |        | o         |
| post_coerce  |                      |              | o      | o         |
| if_invalid   |                      |              |        | o         |

| Schema props | jsonschema           | cerberus     | source | output    |
|--------------|----------------------|--------------|--------|-----------|
| required     | required             | required     | o      |           |
| require_all  |                      | require_all  | o      |           |
| rename       |                      | rename       | orig   | o         |
| synonyms     |                      |              | orig   | o         |
| allow_unkown |                      |              | orig   |           |
| purge_unkown |                      |              |        | o         |
| default      | default              | default      |        | o         |
|        dict: |                      |              |        |           |
| items        | properties           | schema(dict) |        |           |
| pattern_items| patternProperties    |              |        |           |
| keys         | propertyNames        | keysrules    |        |           |
| values       | additionalProperties | valuesrules* |        |           |
|        list: |                      |              |        |           |
| items        | items (list)         | items        |        |           |
| pattern_items| additionalItems      |              |        |           |
| values       | items (dict)         | schema(list) |        |           |
|              | dependencies         | dependencies |        |           |

**Default has precedence over required!**
