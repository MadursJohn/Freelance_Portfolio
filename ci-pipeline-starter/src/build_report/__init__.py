"""
build_report
============
Parse and format CI/CD build log output into structured reports.

Typical usage::

    from build_report import parser, formatter

    result = parser.parse_log("path/to/build.log")
    report = formatter.to_markdown(result)
    print(report)
"""

__version__ = "0.1.0"
__author__ = "João Madureira"
