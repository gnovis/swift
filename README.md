# **Swift - FCA Data Converter** ![](swift_fca/resources/images/swift_icon.ico?raw=true "Swift FCA")

Converter of data formats used in Formal Concept Analysis and public repositories. Swift provides console application and GUI interface.  

## Supported formats
* [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) 
* [ARFF](http://weka.wikispaces.com/ARFF+%28book+version%29)
* [DATA](http://www.cs.washington.edu/dm/vfml/appendixes/c45.htm)
* [DAT](http://fcalgs.sourceforge.net/format.html)
* [CXT](http://www.upriss.org.uk/fca/fcafileformats.html#Burmeister)

## Arguments

### A. Object Names
List of object names sepeprated by: ",", separator inside string isn't allowed.  
Example: `"obj1, obj2, obj3, ... "`  

### B. Attributes  

#### Grammar (BNF with [regular expressions](https://docs.python.org/2/library/re.html))

```
<formula_list> ::= <formula> | <formula> <comma> <formula_list>
<formula> ::= <formula_first_part> <formula_second_part>
<formula_first_part> ::= (<name> "=")? <name>
<formula_second_part> ::= "[" <args>? "]"
<name> ::= \w+
<args> ::= <num_arg> | <enum_arg> | <str_arg> | <date_arg> | <no_scale_arg>
<num_arg> ::= "n" <comma> <num_expr>
<enum_arg> ::= "e" <comma> "'" \w+ "'"
<str_arg> ::= "s" <comma> "'" .+ "'"
<date_arg> ::= "d" <comma> <date_expr> (<comma> "'" .+ "'")?
<expr_var> ::= [a-zA-Z_]
<num_val> ::= "-"? \d
<num_expr> ::= <expr_var> <op> <num_val> |
               <num_val> <op> <expr_var> |
               <num_val> <op> <expr_var> <op> <num_val>
<date_val> ::= "'" .+ "'"
<date_expr> ::= <expr_var> <op> <date_val> |
                <date_val> <op> <expr_var> |
                <date_val> <op> <expr_var> <op> <date_val>
<op> ::= "<" | ">" | "<=" | ">=" | "=="
<no_scale_arg> ::= <no_scale_num> | <no_scale_enum> | <no_scale_str> | <no_scale_date>
<no_scale_num> ::= "n"
<no_scale_enum> ::= "e"
<no_scale_str> ::= "s"
<no_scale_date> ::= "d" <comma> (<comma> "'" .+ "'")?
<comma> ::= ","
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
> Scan through string looking for a location where this regular expression produces a match, and return a corresponding MatchObject instance (Scaling return True). Return None if no position in the string matches the pattern (Scaling return False)  

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


## Requirements
* [python3](https://www.python.org/)
* [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
* [pyparsing](https://pyparsing.wikispaces.com/)
