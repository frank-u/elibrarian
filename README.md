# eLibrarian
[![Build Status](https://travis-ci.org/frank-u/elibrarian.svg?branch=master)](https://travis-ci.org/frank-u/elibrarian)

&nbsp;&nbsp;Keep track of what you reading.

# Purpose
&nbsp;&nbsp;Application intended for users who read books and want to keep track
of currently reading books, keeping track books planned to read and statistics 
about already read books. 


# Project structure (elibrarian-app)
&nbsp;&nbsp;Project consists of flask application, which implements and serves
the REST API for operating with the library.
&nbsp;&nbsp;These basic parts implemented as blueprints:

* **main** - core features.
* **api** - REST API.
* **webui** - Web interface, which will consume API.
