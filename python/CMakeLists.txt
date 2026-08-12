find_package(Python3 COMPONENTS Interpreter Development.Module QUIET)
if(Python3_Interpreter_FOUND)
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -m pybind11 --cmakedir
        OUTPUT_VARIABLE pybind11_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
endif()

find_package(pybind11 CONFIG QUIET)
if(pybind11_FOUND)
    pybind11_add_module(wildfire_env wildfire_env.cpp)
    target_include_directories(wildfire_env PRIVATE "${CMAKE_SOURCE_DIR}/main/include")
    target_link_libraries(wildfire_env PRIVATE cadmium behave)
    target_compile_options(wildfire_env PRIVATE -std=gnu++2b)
    target_compile_definitions(wildfire_env PRIVATE _USE_MATH_DEFINES)
    target_compile_definitions(wildfire_env PRIVATE _SILENCE_ALL_MS_EXT_DEPRECATION_WARNINGS)
else()
    message(STATUS "pybind11 not found -- skipping Python RL bindings (wildfire_env). Run 'pip install pybind11' to enable.")
endif()
