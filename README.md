# Swift - FCA Data Converter
Converter of data formats used in Formal Concept Analysis and public repositories.  
Swift provides command line application and GUI interface.  

## Supported formats
-------------------
* [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) 
* [ARFF](http://weka.wikispaces.com/ARFF+%28book+version%29)
* [DATA](http://www.cs.washington.edu/dm/vfml/appendixes/c45.htm)
* [DAT](http://fcalgs.sourceforge.net/format.html)
* [CXT](http://www.upriss.org.uk/fca/fcafileformats.html#Burmeister)

## Expected parameters
-------------------

### a. Non Scale (attributes and objects)
String with values sepeprated by: ",", separator inside string must be escaped.  
*Use this type, when target file don't need information about parameters type e.g .data -> .csv*  
Example: ```"name, age, sex, nation\,ality"```

String with values and types(s-string, n-numeric, e-enumeration data) separated by: ","  
*Use this type, when target file need information about parameters type e.g .data -> .arff*    
Example: ```"name[s], age[n], sex[e], nation\,ality[s]"```

### b. Scale (attributes)  
Attributes for scaling are compound of formulas seperated by: ","  
Formula in format: ```new_attr=old_attr[expression]identifier```

* new_attr = name of new attribute witch will be the result of a conversion
* old_attr = name of attribute, whitch will be use as template for new attribute
* expression:
    * string (for enumeration data)   
    * regular expression (for string data)  
    * interval (for numeric data) e.g ```x>=50``` or ```100<value<150``` - variable (x and value in example) can be anything except >,<,= and numbers.
* identifier = s - string data, n - numeric data, e - enumeration data

Is possible to write formula in format: ```new_attr=old_attr```, in this case result of scaling will be same value, it works (and make sance) only for binary values 0 and 1  
 
Example: 
```
"scaled_age=age(x<50)i, 
 scaled_sex=sex(woman)e, 
 scaled_height=height(150<=x<=210)i,  
 scaled_same=same,  
 scaled_address=address(\w? street[0-9]+)s"
``` 

### c. Others
e.g separator, classes ...


## Requirements
------------
* python3
* PyQt4