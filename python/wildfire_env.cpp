#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "rl_environment.hpp"

namespace py = pybind11;

PYBIND11_MODULE(wildfire_env, m)
{
    m.doc() = "Python bindings for the hybrid DEVS/Cell-DEVS wildfire simulation, for RL training.";

    py::class_<WildfireEnvironment>(m, "WildfireEnvironment")
        .def(py::init<std::string, double, int>(), py::arg("config_path"), py::arg("sample_period") = 3600.0, py::arg("cells_per_decision") = 5)
        .def("reset", &WildfireEnvironment::reset)
        .def("step", &WildfireEnvironment::step, py::arg("target_cell_ids") = std::vector<std::string>{})
        .def("ignited_cells", &WildfireEnvironment::ignitedCells)
        .def("top_dangerous_cells", &WildfireEnvironment::topDangerousCells)
        .def("close", &WildfireEnvironment::close);
}
