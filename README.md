pytex
=====

**A command line tool to ease the redaction of LaTeX documents.**


Installation
------------

You can use either `pip` or `easy_install` to install the latest `pytex`
release from PyPI:

    pip install pytex

Alternatively, you can download the latest development sources and
install the package manually:

    curl -L -o - https://github.com/GaretJax/pytex/tarball/develop | tar xz
    cd GaretJax-pytex-*
    python setup.py install

or exploit `pip` to install an editable copy locally:

    pip install -e git+https://github.com/GaretJax/pytex.git#egg=pytex


Usage
-----

Help can be obtained by running `pytex --help` to obtain information about
the general usage or `pytex <subcommand> --help` to obtain help about a
specific subcommand.

    $ pytex --help
    usage: pytex [-h] [--version] [-v] [-q]
                 
                 {clean,compile,watch,diff,init,spellcheck,list-templates,update-templates,save,tag}
                 ...
    
    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -v, --verbose         Increments the verbosity (can be used multiple times).
      -q, --quiet           Decrements the verbosity (can be used multiple times).
    
    subcommands:
      {clean,compile,watch,diff,init,spellcheck,list-templates,update-templates,save,tag}
        clean               Clean the document by deleting all files resulted from
                            the building process.
        compile             Compile the LaTeX sources into a PDF document.
        watch               Monitor the current directory for changes and rebuild
                            the document when needed.
        diff                Creates a PDF document highligthing the changes
                            between two tags in the repository.
        init                Creates a new pytex document with the given name.
        spellcheck          Checks every LaTeX source file in the document for
                            spelling errors.
        list-templates      List the currently available templates.
        update-templates    Updates the current templates set by pulling the
                            latest changes from the remote git repository.
        save                Saves the current version of the document in a single
                            commit.
        tag                 Creates a tagged version of the document out of the
                            currently active commit.
