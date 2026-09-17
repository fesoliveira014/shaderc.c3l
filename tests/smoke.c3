module smoke;

import shaderc;

const uint SPIRV_MAGIC = 0x07230203;

fn void main() {
    shaderc::Compiler compiler = shaderc::compiler_create();
    assert(compiler != null);
    defer compiler.release();
    shaderc::CompileOptions options = shaderc::options_create();
    assert(options != null);
    defer options.release();
    options.set_target_env(shaderc::TargetEnv.TARGET_ENV_VULKAN, shaderc::EnvVersion.ENV_VERSION_VULKAN_1_2);
    options.set_target_spirv(shaderc::SpirvVersion.SPIRV_VERSION_1_5);
    options.set_optimization_level(shaderc::OptimizationLevel.OPTIMIZATION_LEVEL_PERFORMANCE);
    options.add_macro_definition(
        name: "SMOKE",
        name_length: 5,
        value: "1",
        value_length: 1,
    );
    options.set_include_callbacks(null, null, null);

    String source = "#version 450\n#if SMOKE != 1\n#error missing macro\n#endif\n"
                    "layout(local_size_x = 1) in;\nvoid main() {}\n";
    shaderc::Result result = compiler.compile_into_spv(
        source_text: source.ptr,
        source_size: source.len,
        kind: shaderc::ShaderKind.COMPUTE_SHADER,
        input_file_name: "smoke.comp",
        entry_point_name: "main",
        options: options,
    );
    assert(result != null);
    defer result.release();
    assert(result.get_compilation_status() == shaderc::CompilationStatus.COMPILATION_STATUS_SUCCESS);
    assert(result.get_num_errors() == 0);
    assert(result.get_length() >= 20 && result.get_length() % 4 == 0);
    assert(*(uint*)result.get_bytes() == SPIRV_MAGIC);

    String invalid_source = "#version 450\n#error expected smoke failure\n";
    shaderc::Result invalid_result = compiler.compile_into_spv(
        source_text: invalid_source.ptr,
        source_size: invalid_source.len,
        kind: shaderc::ShaderKind.COMPUTE_SHADER,
        input_file_name: "invalid.comp",
        entry_point_name: "main",
        options: options,
    );
    assert(invalid_result != null);
    defer invalid_result.release();
    assert(invalid_result.get_compilation_status() != shaderc::CompilationStatus.COMPILATION_STATUS_SUCCESS);
    assert(invalid_result.get_num_errors() > 0);
    assert(invalid_result.get_error_message() != null);
}
