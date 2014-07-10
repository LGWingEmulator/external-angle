//
// Copyright (c) 2014 The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// CollectVariables_test.cpp:
//   Some tests for shader inspection
//

#include "angle_gl.h"
#include "gtest/gtest.h"
#include "GLSLANG/ShaderLang.h"
#include "compiler/translator/TranslatorGLSL.h"

class CollectVariablesTest : public testing::Test
{
  public:
    CollectVariablesTest(GLenum shaderType)
        : mShaderType(shaderType)
    {}

  protected:
    virtual void SetUp()
    {
        ShBuiltInResources resources;
        ShInitBuiltInResources(&resources);
        resources.MaxDrawBuffers = 8;

        mTranslator = new TranslatorGLSL(mShaderType, SH_GLES2_SPEC);
        ASSERT_TRUE(mTranslator->Init(resources));
    }

    virtual void TearDown()
    {
        delete mTranslator;
    }

    GLenum mShaderType;
    TranslatorGLSL *mTranslator;
};

class CollectVertexVariablesTest : public CollectVariablesTest
{
  public:
    CollectVertexVariablesTest() : CollectVariablesTest(GL_VERTEX_SHADER) {}
};

class CollectFragmentVariablesTest : public CollectVariablesTest
{
  public:
      CollectFragmentVariablesTest() : CollectVariablesTest(GL_FRAGMENT_SHADER) {}
};

TEST_F(CollectFragmentVariablesTest, SimpleOutputVar)
{
    const std::string &shaderString =
        "#version 300 es\n"
        "precision mediump float;\n"
        "out vec4 out_fragColor;\n"
        "void main() {\n"
        "   out_fragColor = vec4(1.0);\n"
        "}\n";

    const char *shaderStrings[] = { shaderString.c_str() };
    ASSERT_TRUE(mTranslator->compile(shaderStrings, 1, SH_VARIABLES));

    const std::vector<sh::Attribute> &outputVariables = mTranslator->getOutputVariables();
    ASSERT_EQ(1u, outputVariables.size());

    const sh::Attribute &outputVariable = outputVariables[0];

    EXPECT_EQ(0, outputVariable.arraySize);
    EXPECT_EQ(-1, outputVariable.location);
    EXPECT_EQ(GL_MEDIUM_FLOAT, outputVariable.precision);
    EXPECT_EQ(true, outputVariable.staticUse);
    EXPECT_EQ(GL_FLOAT_VEC4, outputVariable.type);
    EXPECT_EQ("out_fragColor", outputVariable.name);
}

TEST_F(CollectFragmentVariablesTest, LocationOutputVar)
{
    const std::string &shaderString =
        "#version 300 es\n"
        "precision mediump float;\n"
        "layout(location=5) out vec4 out_fragColor;\n"
        "void main() {\n"
        "   out_fragColor = vec4(1.0);\n"
        "}\n";

    const char *shaderStrings[] = { shaderString.c_str() };
    ASSERT_TRUE(mTranslator->compile(shaderStrings, 1, SH_VARIABLES));

    const std::vector<sh::Attribute> &outputVariables = mTranslator->getOutputVariables();
    ASSERT_EQ(1u, outputVariables.size());

    const sh::Attribute &outputVariable = outputVariables[0];

    EXPECT_EQ(0, outputVariable.arraySize);
    EXPECT_EQ(5, outputVariable.location);
    EXPECT_EQ(GL_MEDIUM_FLOAT, outputVariable.precision);
    EXPECT_EQ(true, outputVariable.staticUse);
    EXPECT_EQ(GL_FLOAT_VEC4, outputVariable.type);
    EXPECT_EQ("out_fragColor", outputVariable.name);
}

TEST_F(CollectVertexVariablesTest, LocationAttribute)
{
    const std::string &shaderString =
        "#version 300 es\n"
        "layout(location=5) in vec4 in_Position;\n"
        "void main() {\n"
        "   gl_Position = in_Position;\n"
        "}\n";

    const char *shaderStrings[] = { shaderString.c_str() };
    ASSERT_TRUE(mTranslator->compile(shaderStrings, 1, SH_VARIABLES));

    const std::vector<sh::Attribute> &attributes = mTranslator->getAttributes();
    ASSERT_EQ(1u, attributes.size());

    const sh::Attribute &attribute = attributes[0];

    EXPECT_EQ(0, attribute.arraySize);
    EXPECT_EQ(5, attribute.location);
    EXPECT_EQ(GL_HIGH_FLOAT, attribute.precision);
    EXPECT_EQ(true, attribute.staticUse);
    EXPECT_EQ(GL_FLOAT_VEC4, attribute.type);
    EXPECT_EQ("in_Position", attribute.name);
}

TEST_F(CollectVertexVariablesTest, SimpleInterfaceBlock)
{
    const std::string &shaderString =
        "#version 300 es\n"
        "uniform b {\n"
        "  float f;\n"
        "};"
        "void main() {\n"
        "   gl_Position = vec4(f, 0.0, 0.0, 1.0);\n"
        "}\n";

    const char *shaderStrings[] = { shaderString.c_str() };
    ASSERT_TRUE(mTranslator->compile(shaderStrings, 1, SH_VARIABLES));

    const std::vector<sh::InterfaceBlock> &interfaceBlocks = mTranslator->getInterfaceBlocks();
    ASSERT_EQ(1u, interfaceBlocks.size());

    const sh::InterfaceBlock &interfaceBlock = interfaceBlocks[0];

    EXPECT_EQ(0, interfaceBlock.arraySize);
    EXPECT_EQ(false, interfaceBlock.isRowMajorLayout);
    EXPECT_EQ(sh::BLOCKLAYOUT_SHARED, interfaceBlock.layout);
    EXPECT_EQ("b", interfaceBlock.name);
    EXPECT_EQ(true, interfaceBlock.staticUse);

    ASSERT_EQ(1, interfaceBlock.fields.size());

    const sh::InterfaceBlockField &field = interfaceBlock.fields[0];

    EXPECT_EQ(GL_HIGH_FLOAT, field.precision);
    EXPECT_EQ(true, field.staticUse);
    EXPECT_EQ(GL_FLOAT, field.type);
    EXPECT_EQ("f", field.name);
    EXPECT_EQ(false, field.isRowMajorMatrix);
    EXPECT_EQ(0, field.fields.size());
}
