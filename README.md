# ![](swift_fca/resources/images/swift_icon.ico?raw=true "Swift FCA") **Swift - Relational Data Converter** 

Swift is a converter of data formats used in Formal Concept Analysis (FCA) and public repositories. Swift provides a Command-line `swift-cli.py` and GUI `swift.py` interfaces. Supported formats are: [CSV](https://en.wikipedia.org/wiki/Comma-separated_values),
[ARFF](http://weka.wikispaces.com/ARFF+%28book+version%29),
[DATA](http://www.cs.washington.edu/dm/vfml/appendixes/c45.htm),
[DAT](http://fcalgs.sourceforge.net/format.html),
[CXT](http://www.upriss.org.uk/fca/fcafileformats.html#Burmeister) and
[DTL](http://gnovis.github.io/swift/manual.html#dtl).

For more informations see the project home page http://gnovis.github.io/swift/.

## Installation

<ol>
<li>Make sure that following requirements are installed in your computer:</li>
<ul>
<li>
<a href="https://www.python.org/">Python 3</a>
</li>
<li>
<a href="https://pyparsing.wikispaces.com/">Pyparsing</a>
</li>
<li>
<a href="http://www.riverbankcomputing.co.uk/software/pyqt/intro">PyQt4</a> &ndash; only for graphical user interface (swift.py)  
</li>
</ul>
<li>Download the source.</li>
<li>Unpack the ZIP archive.</li>
<li>Go to the swift folder.</li>
<li>Run swift.</li>
</ol>

## Usage
The simplest scenario of using Swift:

```
cd path/to/swift/
```

```
swift-cli.py input.dat -t output.csv
```
The code above converts the input.dat to the output.csv file. Not every conversion can be used that way, some of them requires additional arguments. For more information about Swift functionality, see the [manual](http://gnovis.github.io/swift/manual.html).

## Contributing
You are welcome to participate in development of this project.

## License
Swift is distributed under the [GNU GPL v3](http://www.gnu.org/licenses/gpl-3.0.html). 
