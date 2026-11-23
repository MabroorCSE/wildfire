#pragma once

#include <memory>
#include <string>
#include <cadmium/core/modeling/coupled.hpp>
#include <cadmium/celldevs/asymm/coupled.hpp>
#include "average_atomic.hpp"
#include "cell.hpp"
#include "state.hpp"
#include "aircraft.hpp"

inline std::shared_ptr<cadmium::celldevs::AsymmCell<State, double>> addWildfireCell(
    const std::string& cellId, const std::shared_ptr<const cadmium::celldevs::AsymmCellConfig<State, double>>& cellConfig)
{
    return std::make_shared<Cell>(cellId, cellConfig);
}

//Hybrid DEVS/Cell-DEVS coupled model: the wildfire Cell-DEVS grid, the RL-side AverageAtomic
//(percent on fire, reward, orders) and one Aircraft. Orders go RL -> aircraft -> cells, so a drop
//reaches its target cell only after the flight time. Aircraft readyOut is not connected yet.
class WildfireHybridCoupled : public cadmium::Coupled
{
public:
    static constexpr const char* wildfireId = "wildfire";
    static constexpr const char* averageModelId = "percentIgnited";
    static constexpr const char* aircraftId = "aircraft";

    std::shared_ptr<AverageAtomic> averageModel;
    std::shared_ptr<Aircraft> aircraft;

    WildfireHybridCoupled(const std::string& id, const std::string& configFilePath, double samplePeriod = 3600.0, int cellsPerDecision = 1, double baseX = 505000, double baseY = 5000600, double tankSize = 1000, double flowRate = 500 , double refillTime = 120)
        : cadmium::Coupled(id)
    {
        auto wildfire = std::make_shared<cadmium::celldevs::AsymmCellDEVSCoupled<State, double>>(
            wildfireId, addWildfireCell, configFilePath);
        wildfire->buildModel();
        addComponent(wildfire);

        averageModel = std::make_shared<AverageAtomic>(averageModelId, samplePeriod, cellsPerDecision);
        aircraft = std::make_shared<Aircraft>(aircraftId, baseX, baseY, tankSize, flowRate, refillTime);
        
        addComponent(averageModel);
        addComponent(aircraft);

        addIC(wildfireId, "cellStateOut", averageModelId, "cellStateIn");
        addIC(averageModelId, "cellCommandOut", aircraftId, "orderIn");
        addIC(aircraftId, "cellCommandOut", wildfireId, "cellCommandIn");

    }
};
