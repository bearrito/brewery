#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .base import Node
from ..ops.iterator import as_records
# from ..ds.csv_streams import CSVDataTarget
import sys

class DataObjectTarget(Node):
    """Generic data object target. Wraps existing target version of `DataObject`
    and appends data from the source.

    Note that this node is only for programatically created processing
    streams. Not useable in visual, web or other stream modelling tools.
    """

    node_info = {
        "label" : "Data Object Target",
        "icon": "row_list_target_nede",
        "description" : "Generic data stream data target node.",
        "attributes" : [
            {
                 "name": "stream",
                 "description": "Data target object."
            }
        ]
    }

    def __init__(self, target):
        super(DataObjectNode, self).__init__()
        self.target = target

    def evaluate(self, context, sources):
        source = sources[0]
        # FIXME: Check for fields compatibility
        self.target.append_from(source)

class DataStreamTarget(DataObjectTarget):
    def __init__(self, stream):
        super(DataStreamTarget, self).__init__(stream)
        logger = get_logger()
        logger.warn("DataStreamTarget is depreciated, use DataObjectTarget "
                    "instead")

class RowListNode(Node):
    """Target node that stores data from input in a list of rows (as tuples).

    To get list of fields, ask for `output_fields`.
    """

    node_info = {
        "label" : "Row List Target",
        "description" : "Store data as list of tuples",
        "attributes" : [
            {
                 "name": "rows",
                 "description": "Created list of tuples."
            }
        ]
    }

    def __init__(self, data=None):
        super(RowListNode, self).__init__()
        if data is not None:
            self.data = data
        else:
            self.data = None

    def evaluate(self, context, sources):
        source = sources[0]

        if not "rows" in source.representations():
            raise Exception("Source %s does not have rows representation" \
                                % source)
        if self.data is not None:
            for row in source.rows():
                self.data.append(row)
        else:
            self.data = list(source.rows())

class RecordListNode(Node):
    """Target node that stores data from input in a list of records (dictionary objects)
    object.

    To get list of fields, ask for `output_fields`.

    """

    node_info = {
        "label" : "Record List Target",
        "description" : "Store data as list of dictionaries (records)",
        "attributes" : [
            {
                 "name": "records",
                 "description": "Created list of records represented as dictionaries."
            }
        ]
    }
    def __init__(self, data=None):
        super(RecordListNode, self).__init__()
        if data is not None:
            self.data = data
        else:
            data = None

    def evaluate(self, context, sources):
        source = sources[0]

        if "records" in source.representations():
            iterator = source.records()
        else:
            iterator = as_records(source.rows(), source.fields)

        if self.data is not None:
            for row in iterator:
                self.data.append(row)
        else:
            self.data = list(iterator)

class CSVNode(Node):
    """Node that writes rows into a comma separated values (CSV) file.

    :Attributes:
        * resource: target object - might be a filename or file-like object
        * write_headers: write field names as headers into output file
        * truncate: remove data from file before writing, default: True

    """
    node_info = {
        "label" : "CSV Target",
        "description" : "Write rows as comma separated values into a file",
        "attributes" : [
            {
                 "name": "resource",
                 "description": "Target object - file name or IO object."
            },
            {
                 "name": "write_headers",
                 "description": "Flag determining whether to write field names as file headers."
            },
            {
                 "name": "truncate",
                 "description": "If set to ``True`` all data from file are removed. Default ``True``"
            }
        ]
    }

    def __init__(self, resource = None, *args, **kwargs):
        super(CSVNode, self).__init__()
        self.resource = resource
        self.args = args
        self.kwargs = kwargs

    def evaluate(self, context, sources):
        source = sources[0]
        self.target = CSVDataTarget(self.resource, fields=source.fields,
                               *self.args, **self.kwargs)

        self.target.append_from(source)

    def finalize(self):
        self.target.flush()


class FormattedPrinterNode(Node):
    """Target node that will print output based on format.

    Refer to the python formatting guide:

        http://docs.python.org/library/string.html

    Example:

    Consider we have a data with information about donations. We want to pretty print two fields:
    `project` and `requested_amount` in the form::

        Hlavicka - makovicka                                            27550.0
        Obecna kniznica - symbol moderneho vzdelavania                 132000.0
        Vzdelavanie na europskej urovni                                 60000.0

    Node for given format is created by:

    .. code-block:: python

        node = FormattedPrinterNode(format = u"{project:<50.50} {requested_amount:>20}")

    Following format can be used to print output from an audit node:

    .. code-block:: python

        node.header = u"field                            nulls      empty   distinct\\n" \\
                       "------------------------------------------------------------"
        node.format = u"{field_name:<30.30} {null_record_ratio: >7.2%} "\\
                       "{empty_string_count:>10} {distinct_count:>10}"

    Output will look similar to this::

        field                            nulls      empty   distinct
        ------------------------------------------------------------
        file                             0.00%          0         32
        source_code                      0.00%          0          2
        id                               9.96%          0        907
        receiver_name                    9.10%          0       1950
        project                          0.05%          0       3628
        requested_amount                22.90%          0        924
        received_amount                  4.98%          0        728
        source_comment                  99.98%          0          2

    """

    node_info = {
        "label" : "Formatted Printer",
        "icong": "formatted_printer_node",
        "description" : "Print input using a string formatter to an output IO stream",
        "attributes" : [
            {
                 "name": "format",
                 "description": "Format string to be used. Default is to print all field values "
                                "separated by tab character."
            },
            {
                 "name": "target",
                 "description": "IO object. If not set then sys.stdout will be used. "
                                "If it is a string, then it is considered a filename."
            },
            {
                 "name": "delimiter",
                 "description": "Record delimiter. By default it is new line character."
            },
            {
                 "name": "header",
                 "description": "Header string - will be printed before printing first record"
            },
            {
                 "name": "footer",
                 "description": "Footer string - will be printed after all records are printed"
            }
        ]
    }
    def __init__(self, format=None, target=sys.stdout, delimiter=None,
                 header=None, footer=None):
        super(FormattedPrinterNode, self).__init__()
        self.format = format

        self.target = target
        self.header = header
        self.footer = footer

        if delimiter:
            self.delimiter = delimiter
        else:
            self.delimiter = '\n'

        self.handle = None
        self.close_handle = False

    def evaluate(self, context, sources):
        source = sources[0]
        names = source.fields.names()

        if type(self.target) == str or type(self.target) == unicode:
            self.handle = open(self.target, "w")
            self.close_handle = True
        else:
            self.handle = self.target
            self.close_handle = False

        if self.format:
            format_string = self.format
        else:
            fields = []
            for name in names:
                fields.append(u"{" + name + u"}")

            format_string = u"" + u"\t".join(fields)

        if self.header is not None:
            self.handle.write(self.header)
            if self.delimiter:
                self.handle.write(self.delimiter)
        else:
            header_string = u"" + u"\t".join(names)
            self.handle.write(header_string)
            if self.delimiter:
                self.handle.write(self.delimiter)

        if "records" in source.representations():
            iterator = source.records()
        else:
            iterator = as_records(source.rows(), source.fields)

        for record in iterator:
            self.handle.write(format_string.format(**record).encode("utf-8"))

            if self.delimiter:
                self.handle.write(self.delimiter)

        if self.footer:
            self.handle.write(self.footer)
            if self.delimiter:
                self.handle.write(self.delimiter)

        self.handle.flush()

    def finalize(self):
        if self.handle:
            self.handle.flush()
            if self.close_handle:
                self.handle.close()

class PrettyPrinterNode(Node):
    """Target node that will pretty print output as a table.
    """

    node_info = {
        "label" : "Pretty Printer",
        "icong": "formatted_printer_node",
        "description" : "Print input using a pretty formatter to an output IO stream",
        "attributes" : [
            {
                 "name": "target",
                 "description": "IO object. If not set then sys.stdout will be used. "
                                "If it is a string, then it is considered a filename."
            },
            {
                 "name": "max_column_width",
                 "description": "Maximum column width. Default is unlimited. "\
                                "If set to None, then it is unlimited."
            },
            {
                 "name": "min_column_width",
                 "description": "Minimum column width. Default is 0 characters."
            }# ,
            #             {
            #                  "name": "sample",
            #                  "description": "Number of records to sample to get column width"
            #             },
        ]
    }
    def __init__(self, target=sys.stdout, max_column_width=None,
                 min_column_width=0, sample=None,
                 print_names=True, print_labels=False):

        super(PrettyPrinterNode, self).__init__()

        self.max_column_width = max_column_width
        self.min_column_width = min_column_width or 0
        self.sample = sample
        self.print_names = print_names
        self.print_labels = print_labels

        self.target = target
        self.handle = None
        self.close_handle = False

    # def initialize_fields(self, sources):

    #     self.widths = [0] * len(sources[0])
    #     self.names = sources[0].names()
    #     if self.print_names:
    #         self.labels = [f.label for f in sources[0]]
    #     else:
    #         self.labels = [f.label or f.name for f in sources[0]]

    #     self._update_widths(self.names)
    #     if self.print_labels:
    #         self._update_widths(self.labels)


    def _update_widths(self, row):
        for i, value in enumerate(row):
            self.widths[i] = max(self.widths[i], len(unicode(value)))

    def evaluate(self, context, sources):
        source = sources[0]
        fields = source.fields

        # initialize fields
        self.widths = [0] * len(fields)
        self.names = fields.names()
        if self.print_names:
            self.labels = [f.label for f in fields]
        else:
            self.labels = [f.label or f.name for f in fields]

        self._update_widths(self.names)
        if self.print_labels:
            self._update_widths(self.labels)

        # initialize file
        if type(self.target) == str or type(self.target) == unicode:
            self.handle = open(self.target, "w")
            self.close_handle = True
        else:
            self.handle = self.target
            self.close_handle = False

        rows = list(sources[0].rows())
        for row in rows:
            self._update_widths(row)

        #
        # Create template
        #

        if self.max_column_width:
            self.widths = [min(w, self.max_column_width) for w in self.widths]
        self.widths = [max(w, self.min_column_width) for w in self.widths]
        fields = [u"{%d:%d}" % (i, w) for i,w in enumerate(self.widths)]
        template = u"|" + u"|".join(fields) + u"|\n"

        field_borders = [u"-"*w for w in self.widths]
        self.border = u"+" + u"+".join(field_borders) + u"+\n"

        self.handle.write(self.border)
        if self.print_names:
            self.handle.write(template.format(*self.names))
        if self.print_labels:
            self.handle.write(template.format(*self.labels))

        if self.print_names or self.print_labels:
            self.handle.write(self.border)

        for row in rows:
            self.handle.write(template.format(*row))

        self.handle.write(self.border)

        self.handle.flush()

    def run(self, sources, target):

        rows = sources[0]

        for row in rows:
            self._update_widths(row)

        #
        # Create template
        #

        if self.max_column_width:
            self.widths = [min(w, self.max_column_width) for w in self.widths]
        self.widths = [max(w, self.min_column_width) for w in self.widths]
        fields = [u"{%d:%d}" % (i, w) for i,w in enumerate(self.widths)]
        template = u"|" + u"|".join(fields) + u"|\n"

        field_borders = [u"-"*w for w in self.widths]
        self.border = u"+" + u"+".join(field_borders) + u"+\n"

        self.handle.write(self.border)
        if self.print_names:
            self.handle.write(template.format(*self.names))
        if self.print_labels:
            self.handle.write(template.format(*self.labels))

        if self.print_names or self.print_labels:
            self.handle.write(self.border)

        for row in rows:
            self.handle.write(template.format(*row))

        self.handle.write(self.border)

        self.handle.flush()

    def finalize(self):
        if self.handle:
            self.handle.flush()
            if self.close_handle:
                self.handle.close()

