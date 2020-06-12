#!/usr/bin/python
# Copyright 2015 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# gen_load_functions_table.py:
#  Code generation for the load function tables used for texture formats. These mappings are
#  not renderer specific. The mappings are done from the GL internal format, to the ANGLE
#  format ID, and then for the specific data type.
#  NOTE: don't run this script directly. Run scripts/run_code_generation.py.
#

import json, sys
from datetime import date

sys.path.append('../..')
import angle_format

template = """// GENERATED FILE - DO NOT EDIT.
// Generated by gen_load_functions_table.py using data from load_functions_data.json
//
// Copyright {copyright_year} The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// load_functions_table:
//   Contains the GetLoadFunctionsMap for texture_format_util.h
//

#include "libANGLE/renderer/load_functions_table.h"

#include "image_util/copyimage.h"
#include "image_util/generatemip.h"
#include "image_util/loadimage.h"

using namespace rx;

namespace angle
{{

namespace
{{

// ES3 image loading functions vary based on:
//    - the GL internal format (supplied to glTex*Image*D)
//    - the GL data type given (supplied to glTex*Image*D)
//    - the target DXGI_FORMAT that the image will be loaded into (which is chosen based on the D3D
//    device's capabilities)
// This map type determines which loading function to use, based on these three parameters.
// Source formats and types are taken from Tables 3.2 and 3.3 of the ES 3 spec.
void UnimplementedLoadFunction(size_t width,
                               size_t height,
                               size_t depth,
                               const uint8_t *input,
                               size_t inputRowPitch,
                               size_t inputDepthPitch,
                               uint8_t *output,
                               size_t outputRowPitch,
                               size_t outputDepthPitch)
{{
    UNIMPLEMENTED();
}}

void UnreachableLoadFunction(size_t width,
                             size_t height,
                             size_t depth,
                             const uint8_t *input,
                             size_t inputRowPitch,
                             size_t inputDepthPitch,
                             uint8_t *output,
                             size_t outputRowPitch,
                             size_t outputDepthPitch)
{{
    UNREACHABLE();
}}

{load_functions_data}}}  // namespace

LoadFunctionMap GetLoadFunctionsMap(GLenum {internal_format}, FormatID {angle_format})
{{
    // clang-format off
    switch ({internal_format})
    {{
{switch_data}
        default:
            break;
    }}
    // clang-format on
    ASSERT(internalFormat == GL_NONE || angleFormat == angle::FormatID::NONE);
    static LoadFunctionMap emptyLoadFunctionsMap;
    return emptyLoadFunctionsMap;

}}  // GetLoadFunctionsMap

}}  // namespace angle
"""

internal_format_param = 'internalFormat'
angle_format_param = 'angleFormat'
angle_format_unknown = 'NONE'


def load_functions_name(internal_format, angle_format):
    return internal_format[3:] + "_to_" + angle_format


def unknown_func_name(internal_format):
    return load_functions_name(internal_format, "default")


def get_load_func(func_name, type_functions):
    snippet = "LoadImageFunctionInfo " + func_name + "(GLenum type)\n"
    snippet += "{\n"
    snippet += "    switch (type)\n"
    snippet += "    {\n"
    for gl_type, load_function in sorted(type_functions.iteritems()):
        snippet += "        case " + gl_type + ":\n"
        requiresConversion = str('LoadToNative<' not in load_function).lower()
        snippet += "            return LoadImageFunctionInfo(" + load_function + ", " + requiresConversion + ");\n"
    snippet += "        default:\n"
    snippet += "            UNREACHABLE();\n"
    snippet += "            return LoadImageFunctionInfo(UnreachableLoadFunction, true);\n"
    snippet += "    }\n"
    snippet += "}\n"
    snippet += "\n"

    return snippet


def get_unknown_load_func(angle_to_type_map, internal_format):
    assert angle_format_unknown in angle_to_type_map
    return get_load_func(
        unknown_func_name(internal_format), angle_to_type_map[angle_format_unknown])


def parse_json(json_data):
    table_data = ''
    load_functions_data = ''
    for internal_format, angle_to_type_map in sorted(json_data.iteritems()):

        s = '        '

        table_data += s + 'case ' + internal_format + ':\n'

        do_switch = len(
            angle_to_type_map) > 1 or angle_to_type_map.keys()[0] != angle_format_unknown

        if do_switch:
            table_data += s + '{\n'
            s += '    '
            table_data += s + 'switch (' + angle_format_param + ')\n'
            table_data += s + '{\n'
            s += '    '

        for angle_format, type_functions in sorted(angle_to_type_map.iteritems()):

            if angle_format == angle_format_unknown:
                continue

            func_name = load_functions_name(internal_format, angle_format)

            # Main case statements
            table_data += s + 'case FormatID::' + angle_format + ':\n'
            table_data += s + '    return ' + func_name + ';\n'

            if angle_format_unknown in angle_to_type_map:
                for gl_type, load_function in angle_to_type_map[angle_format_unknown].iteritems():
                    if gl_type not in type_functions:
                        type_functions[gl_type] = load_function

            load_functions_data += get_load_func(func_name, type_functions)

        if do_switch:
            table_data += s + 'default:\n'

        has_break_in_switch = False
        if angle_format_unknown in angle_to_type_map:
            table_data += s + '    return ' + unknown_func_name(internal_format) + ';\n'
            load_functions_data += get_unknown_load_func(angle_to_type_map, internal_format)
        else:
            has_break_in_switch = True
            table_data += s + '    break;\n'

        if do_switch:
            s = s[4:]
            table_data += s + '}\n'
            if has_break_in_switch:
                # If the inner switch contains a break statement, add a break
                # statement after the switch as well.
                table_data += s + 'break;\n'
            s = s[4:]
            table_data += s + '}\n'

    return table_data, load_functions_data


def main():

    # auto_script parameters.
    if len(sys.argv) > 1:
        inputs = ['angle_format.py', 'load_functions_data.json']
        outputs = ['load_functions_table_autogen.cpp']

        if sys.argv[1] == 'inputs':
            print ','.join(inputs)
        elif sys.argv[1] == 'outputs':
            print ','.join(outputs)
        else:
            print('Invalid script parameters')
            return 1
        return 0

    json_data = angle_format.load_json('load_functions_data.json')

    switch_data, load_functions_data = parse_json(json_data)
    output = template.format(
        internal_format=internal_format_param,
        angle_format=angle_format_param,
        switch_data=switch_data,
        load_functions_data=load_functions_data,
        copyright_year=date.today().year)

    with open('load_functions_table_autogen.cpp', 'wt') as out_file:
        out_file.write(output)
        out_file.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
