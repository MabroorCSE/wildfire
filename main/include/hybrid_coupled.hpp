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

//Hybrid DEVS/Cell-DEVS coupled model: the wildfire Cell-DEVS grid plus one atomic model
//connected to every cell (percent on fire, reward, and a command channel targeting any cell).
class WildfireHybridCoupled : public cadmium::Coupled
{
public:
    static constexpr const char* wildfireId = "wildfire";
    static constexpr const char* averageModelId = "percentIgnited";

    std::shared_ptr<AverageAtomic> averageModel;

    WildfireHybridCoupled(const std::string& id, const std::string& configFilePath, double samplePeriod = 3600.0, int cellsPerDecision = 1)
        : cadmium::Coupled(id)
    {
        auto wildfire = std::make_shared<cadmium::celldevs::AsymmCellDEVSCoupled<State, double>>(
            wildfireId, addWildfireCell, configFilePath);
        wildfire->buildModel();
        addComponent(wildfire);

        averageModel = std::make_shared<AverageAtomic>(averageModelId, samplePeriod, cellsPerDecision);
        addComponent(averageModel);

        addIC(wildfireId, "cellStateOut", averageModelId, "cellStateIn");
        addIC(averageModelId, "cellCommandOut", wildfireId, "cellCommandIn");
    }
};
