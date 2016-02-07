# **Swift - FCA Data Converter** ![](swift_fca/resources/images/swift_icon.ico?raw=true "Swift FCA")

Converter of data formats used in Formal Concept Analysis and public repositories. Swift provides console application and GUI interface.  

## Supported formats
* [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) 
* [ARFF](http://weka.wikispaces.com/ARFF+%28book+version%29)
* [DATA](http://www.cs.washington.edu/dm/vfml/appendixes/c45.htm)
* [DAT](http://fcalgs.sourceforge.net/format.html)
* [CXT](http://www.upriss.org.uk/fca/fcafileformats.html#Burmeister)

## Options

usage: swift [-h] [-ss SOURCE_SEPARATOR] [-ta TARGET_ATTRIBUTES] [-i]
             [-mv MISSING_VALUE] [-snh] [-tnh] [-t [TARGET]]
             [-ts TARGET_SEPARATOR] [-to TARGET_OBJECTS] [-n NAME]
             [-cls CLASSES] [-sf {csv,arff,dat,data,cxt,dtl}]
             [-tf {csv,arff,dat,data,cxt,dtl}] [-c [CONVERT]] [-p [PREVIEW]]
             [-sl SKIPPED_LINES] [-se] [-scs SOURCE_CLS_SEPARATOR]
             [-tcs TARGET_CLS_SEPARATOR]
             [source]

Swift is a Relational Data Converter of data formats used in Formal Concept
Analysis (FCA) and public repositories.

positional arguments:
  source                Name of source file.

optional arguments:
  -h, --help            show this help message and exit
  -ss SOURCE_SEPARATOR, --source_separator SOURCE_SEPARATOR
                        Separator which is used in source file. Default is
                        ','.
  -ta TARGET_ATTRIBUTES, --target_attributes TARGET_ATTRIBUTES
                        Attributes Formula used for filtering, reordering and
                        converting attributes.
  -i, --info            Print information about source file data.
  -mv MISSING_VALUE, --missing_value MISSING_VALUE
                        Character which is used in data as value for non-
                        specified attribute.
  -snh, --source_no_header
                        Attributes aren't specified on first line in csv data
                        file.
  -tnh, --target_no_header
                        Attributes wont't be specified on first line in csv
                        data file.
  -t [TARGET], --target [TARGET]
                        Name of target file.
  -ts TARGET_SEPARATOR, --target_separator TARGET_SEPARATOR
                        Separator which will be used in target file. Default
                        is ','.
  -to TARGET_OBJECTS, --target_objects TARGET_OBJECTS
                        Target file (new) objects. Only for CXT format.
  -n NAME, --name NAME  New name of relation.
  -cls CLASSES, --classes CLASSES
                        Intervals (e.g 5-8) or keys, seperated by commas. For
                        determine, which attribute will be used as class.
                        Compulsory for coversion: -> C4.5 and -> DTL.
  -sf {csv,arff,dat,data,cxt,dtl}, --source_format {csv,arff,dat,data,cxt,dtl}
                        Format of source file, must to be specified when
                        source is standart input (stdin)
  -tf {csv,arff,dat,data,cxt,dtl}, --target_format {csv,arff,dat,data,cxt,dtl}
                        Format of target file, must to be specified when
                        target is standart output (stdout)
  -c [CONVERT], --convert [CONVERT]
                        Source file will be converted to target file, this is
                        default option.
  -p [PREVIEW], --preview [PREVIEW]
                        Desired count of lines from source file will be
                        displayed.
  -sl SKIPPED_LINES, --skipped_lines SKIPPED_LINES
                        Interval of lines which will be skipped in any
                        operation.
  -se, --skip_errors    Skip broken lines, which cause an errors.
  -scs SOURCE_CLS_SEPARATOR, --source_cls_separator SOURCE_CLS_SEPARATOR
                        Separator which separates attributes and classes in
                        source (will be read) C4.5 file format.
  -tcs TARGET_CLS_SEPARATOR, --target_cls_separator TARGET_CLS_SEPARATOR
                        Separator which separates attributes and classes in
                        target (will be written) C4.5 file format.
<!---
### A. Object Names
List of object names sepeprated by: ",", separator inside string isn't allowed.  
Example: `"obj1, obj2, obj3, ... "`  
### A. Target Attributes - specification of scale/copy formula

#### Grammar (BNF with [regular expressions](https://docs.python.org/2/library/re.html))

```
<formulas> ::= <formula> | (<formula> ";" <formulas>)
<formula> ::= (<names> "=")? <names> ((":" <type> ("[" <scale>? "]")?) | "[]")?
<names> ::= <name> | (<name> "," <names>)
<type> ::= "n" | "e" | "s" | ("d" ("/" <date_format>)?)
<scale> ::= <num_scale> | <enum_scale> | <str_scale> | <date_scale> | <bin_vals>
<name> ::= \w+ | ((\d+)? "-" (\d+)?) | "*"
<date_format> ::= "F="? "'" .+ "'"
<num_scale> ::= (<var> <op> <num_val>) | (<num_val> <op> <var>) |
                (<num_val> <op> <var> <op> <num_val>)
<enum_scale> ::= "'" \w+ "'"
<str_scale> ::= "'" .+ "'"
<date_scale> ::= ((<var> <op> <date_val>) | (<date_val> <op> <var>) |
                 (<date_val> <op> <var> <op> <date_val>))
<bin_vals> ::= ("0="? "'" .* "'" ",")? "1="? "'" .+ "'"
<var> ::= [a-zA-Z_]+
<op> ::= "<" | ">" | "<=" | ">=" | "==" | "!="
<num_val> ::= "-"? \d+
<date_val> ::= "'" .+ "'"
```
*Notes: Every token can be surrounded by any amount of white spaces. In grammar are white spaces omitted because of better readability.*  
**Attributes**  
Attributes are compound of formulas separated by: ","  

**Formula**  
Formula has format: `new_name=old_name[arguments]` or `old_name[arguments]`  

`new_name` = name of new attribute which will be the result of a conversion. If this new name and `=` is ommited, name of scaled attribute will be old name.  
`old_name` = name of attribute, which will be use as template for new attribute  
`arguments` = list of arguments separated by "," which depends on attribute type or can be omitted (explanation below)  

Attribute Type is on a first position of `arguments`:

* s - String
* n - Numeric
* e - Enumeration 
* d - Date  

Valid syntax of formula is also: `new_attr=old_attr[]`, in this case result of scaling will be same value, it works (and make seance) only for binary values 0 and 1  

**String Attribute**  
`attributes = s, 'regular_expression'`   
`regular_expression`: must be surrounded by quotes. Supported syntax is described here: [python regex](https://docs.python.org/2/library/re.html)  
For Scaling is used `re.RegexObject.search` method.  
Description from [documentation](https://docs.python.org/2/library/re.html#re.RegexObject.search):  
Scan through string looking for a location where this regular expression produces a match, and return a corresponding MatchObject instance (Scaling return True). Return None if no position in the string matches the pattern (Scaling return False)  

**Numeric Attribute**  
`attributes = n, bool_expression`  
`bool_expression`: is compound of variable(any alphas name), number, and operators(`<`, `>`, `>=`, `<=`, `==`), allowed are following forms:

* variable operator number -> `var >= 50`
* number operator variable -> `66 == var`
* number operator variable operator number -> `10 < var < 100`

**Enumeration Attribute**  
`attributes = e, pattern`  
`pattern`: literal which exact match one of item in enumeration  

**Date Attribute**  
`attributes = d, bool_expr, 'date_format'`  
`bool_expr`: has same syntax as bool_expr in Numeric Attribute, but number is Unix Time Stamp  
`date_format`: must be surrounded by quotes. Supported syntax is described here: [python datetime](https://docs.python.org/2/library/datetime.html#module-datetime)
 
Example: 
```
"scaled_age=age[n, x<50], 
 scaled_sex=sex[e, woman], 
 scaled_height=height[n, 150<=x<=210],  
 scaled_same=same[],
 old_name[n, val>50], 
 scaled_address=address[s, '\w? street[0-9]+'],
 scaled_birthday=birthday[d, date > 1000, '%H:%M:%S %Z']"
```

### C. Others
e.g separator, classes,  ...
-->

## Requirements
* [python3](https://www.python.org/)
* [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
* [pyparsing](https://pyparsing.wikispaces.com/)
