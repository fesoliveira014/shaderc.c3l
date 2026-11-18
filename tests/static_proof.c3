module static_proof;

import shaderc;
import std::io;

const uint SPIRV_MAGIC = 0x07230203;
const uint OP_CAPABILITY = 17;
const uint CAPABILITY_DEMOTE_TO_HELPER_INVOCATION = 5379;

const String VERTEX_SOURCE = "#version 450\n"
    "layout(location = 0) in vec3 position;\n"
    "void main() { gl_Position = vec4(position, 1.0); }\n";

const String FRAGMENT_SOURCE = "#version 450\n"
    "layout(location = 0) in float alpha;\n"
    "layout(location = 0) out vec4 color;\n"
    "void main() {\n"
    "    if (alpha < 0.5) discard;\n"
    "    color = vec4(1.0);\n"
    "}\n";

const String COMPUTE_SOURCE = "#version 450\n"
    "#extension GL_GOOGLE_include_directive : require\n"
    "#include \"common.glsl\"\n"
    "layout(local_size_x = GROUP_SIZE) in;\n"
    "layout(std430, binding = 0) buffer Output { uint values[]; };\n"
    "void main() { values[gl_GlobalInvocationID.x] = twice(gl_GlobalInvocationID.x); }\n";

const String COMMON_INCLUDE = "#define GROUP_SIZE 64\nuint twice(uint x) { return x * 2u; }\n";

const String BROKEN_SOURCE = "#version 450\n"
    "void main() {\n"
    "    int broken = ;\n"
    "}\n";

int failures;
int include_resolves;
int include_releases;
shaderc::IncludeResult include_result;

fn void expect(bool condition, String what)
{
    if (condition)
    {
        io::printfn("ok   %s", what);
        return;
    }
    io::printfn("FAIL %s", what);
    failures++;
}

fn shaderc::IncludeResult* resolve_include(void* user_data, char* requested_source, shaderc::IncludeType type, char* requesting_source, usz include_depth)
{
    include_resolves++;
    ZString requested = (ZString)requested_source;
    if (requested.str_view() == "common.glsl")
    {
        include_result.source_name = "common.glsl";
        include_result.source_name_length = 11;
        include_result.content = COMMON_INCLUDE.ptr;
        include_result.content_length = COMMON_INCLUDE.len;
    }
    else
    {
        include_result.source_name = "";
        include_result.source_name_length = 0;
        include_result.content = "not found";
        include_result.content_length = 9;
    }
    include_result.user_data = user_data;
    return &include_result;
}

fn void release_include(void* user_data, shaderc::IncludeResult* result)
{
    include_releases++;
}

fn bool has_demote_capability(char* bytes, usz length)
{
    uint* words = (uint*)bytes;
    usz count = length / 4;
    usz index = 5;
    while (index < count)
    {
        uint word_count = words[index] >> 16;
        uint opcode = words[index] & 0xFFFF;
        if (word_count == 0) return false;
        if (opcode == OP_CAPABILITY && words[index + 1] == CAPABILITY_DEMOTE_TO_HELPER_INVOCATION) return true;
        index += word_count;
    }
    return false;
}

fn shaderc::Result compile(shaderc::Compiler compiler, shaderc::CompileOptions options, String source, shaderc::ShaderKind kind, ZString file_name)
{
    return compiler.compile_into_spv(
        source_text: source.ptr,
        source_size: source.len,
        kind: kind,
        input_file_name: file_name,
        entry_point_name: "main",
        options: options,
    );
}

fn bool is_spirv(shaderc::Result result)
{
    return result.get_compilation_status() == shaderc::CompilationStatus.COMPILATION_STATUS_SUCCESS
        && result.get_length() >= 20
        && result.get_length() % 4 == 0
        && *(uint*)result.get_bytes() == SPIRV_MAGIC;
}

fn int main()
{
    uint version;
    uint revision;
    shaderc::get_spv_version(&version, &revision);
    io::printfn("spirv version 0x%x revision %d", version, revision);
    expect(version >= 0x010500, "shaderc_get_spv_version reports at least SPIR-V 1.5");

    shaderc::Compiler compiler = shaderc::compiler_create();
    expect(compiler != null, "compiler initialize");
    defer compiler.release();

    shaderc::CompileOptions options = shaderc::options_create();
    expect(options != null, "options initialize");
    defer options.release();
    options.set_source_language(shaderc::SourceLanguage.SOURCE_LANGUAGE_GLSL);
    options.set_target_env(shaderc::TargetEnv.TARGET_ENV_VULKAN, shaderc::EnvVersion.ENV_VERSION_VULKAN_1_2);
    options.set_target_spirv(shaderc::SpirvVersion.SPIRV_VERSION_1_5);
    options.set_optimization_level(shaderc::OptimizationLevel.OPTIMIZATION_LEVEL_PERFORMANCE);
    options.set_generate_debug_info();
    options.add_macro_definition(
        name: "PROOF",
        name_length: 5,
        value: "1",
        value_length: 1,
    );
    options.set_include_callbacks(&resolve_include, &release_include, null);

    shaderc::Result vertex = compile(compiler, options, VERTEX_SOURCE, shaderc::ShaderKind.VERTEX_SHADER, "proof.vert");
    defer vertex.release();
    expect(is_spirv(vertex), "vertex shader compiles to SPIR-V");

    shaderc::Result fragment = compile(compiler, options, FRAGMENT_SOURCE, shaderc::ShaderKind.FRAGMENT_SHADER, "proof.frag");
    defer fragment.release();
    expect(is_spirv(fragment), "fragment shader with discard compiles to SPIR-V");
    expect(!has_demote_capability(fragment.get_bytes(), fragment.get_length()), "fragment module declares no DemoteToHelperInvocation capability");

    shaderc::Result compute = compile(compiler, options, COMPUTE_SOURCE, shaderc::ShaderKind.COMPUTE_SHADER, "proof.comp");
    defer compute.release();
    expect(is_spirv(compute), "compute shader compiles through the include callbacks");
    expect(include_resolves == 1, "the resolve callback ran once");
    expect(include_releases == 1, "the release callback ran once");

    shaderc::Result broken = compile(compiler, options, BROKEN_SOURCE, shaderc::ShaderKind.FRAGMENT_SHADER, "broken.frag");
    defer broken.release();
    expect(broken.get_compilation_status() == shaderc::CompilationStatus.COMPILATION_STATUS_COMPILATION_ERROR, "a syntax error fails with a compilation error");
    expect(broken.get_num_errors() > 0, "the syntax error is counted");
    ZString message = (ZString)broken.get_error_message();
    io::printfn("error message: %s", message);
    expect(message.str_view().starts_with("broken.frag:3:"), "the syntax error is reported as file:line");

    io::printfn("warnings in the vertex shader: %d", vertex.get_num_warnings());
    if (failures > 0)
    {
        io::printfn("%d checks failed", failures);
        return 1;
    }
    io::printn("static proof passed");
    return 0;
}
