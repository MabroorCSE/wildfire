#pragma once

#include <memory>
#include <string>
#include <cadmium/core/modeling/coupled.hpp>
#include <cadmium/celldevs/asymm/coupled.hpp>
#include "average_atomic.hpp"
#include "cell.hpp"
#include "state.hpp"

inline std::shared_ptr<cadmium::celldevs::AsymmCell<State, double>> addWildfireCell(
    const std::string& cellId, const std::shared_ptr<const cadmium::celldevs::AsymmCellConfig<State, double>>& cellConfig)
{
    return std::make_shared<Cell>(cellId, cellConfig);
}

//Top-level hybrid DEVS/Cell-DEVS coupled model. It embeds the existing wildfire Cell-DEVS
//coupled model unchanged, plus a plain atomic DEVS model connected to every cell.
//The wildfire model exposes every cell's output through a single shared external output
//coupling port ("cellStateOut"), declared once in each map's "default" cell config.
class WildfireHybridCoupled : public cadmium::Coupled
{
public:
    static constexpr const char* wildfireId = "wildfire";
    static constexpr const char* averageModelId = "percentIgnited";

    WildfireHybridCoupled(const std::string& id, const std::string& configFilePath)
        : cadmium::Coupled(id)
    {
        auto wildfire = std::make_shared<cadmium::celldevs::AsymmCellDEVSCoupled<State, double>>(
            wildfireId, addWildfireCell, configFilePath);
        wildfire->buildModel();
        addComponent(wildfire);

        auto averageModel = std::make_shared<AverageAtomic>(averageModelId);
        addComponent(averageModel);

        addIC(wildfireId, "cellStateOut", averageModelId, "cellStateIn");
    }
};
