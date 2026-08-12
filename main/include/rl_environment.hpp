#pragma once

#include <memory>
#include <string>
#include <vector>
#include <cadmium/core/simulation/root_coordinator.hpp>
#include "hybrid_coupled.hpp"

//Step-by-step driver for the hybrid model, used by the pybind11 bindings (python/wildfire_env.cpp).
//RootCoordinator::simulate(timeInterval) advances relative to the current time, so calling it
//once per samplePeriod steps the simulation one decision at a time instead of running it whole.
class WildfireEnvironment
{
public:
    explicit WildfireEnvironment(std::string configFilePath, double samplePeriod = 3600.0, int cellsPerDecision = 1)
        : configFilePath(std::move(configFilePath)), samplePeriod(samplePeriod), cellsPerDecision(cellsPerDecision)
    {
        reset();
    }

    double reset()
    {
        model = std::make_shared<WildfireHybridCoupled>("wildfireEnv", configFilePath, samplePeriod, cellsPerDecision);
        coordinator = std::make_unique<cadmium::RootCoordinator>(model);
        coordinator->start();
        return model->averageModel->lastPercentIgnited();
    }

    //targetCellIds: cells to extinguish this step (0 to N), empty means do nothing.
    std::pair<double, double> step(std::vector<std::string> targetCellIds)
    {
        model->averageModel->requestActions(targetCellIds);
        //simulate() uses timeNext < timeFinal (strict), so without the epsilon the tick landing
        //exactly at samplePeriod would never fire and output() would never run.
        coordinator->simulate(samplePeriod + 1e-6);
        return {model->averageModel->lastPercentIgnited(), model->averageModel->lastReward()};
    }

    std::vector<std::string> ignitedCells() const
    {
        return model->averageModel->ignitedCellIds();
    }

    std::vector<std::string> topDangerousCells() const
    {
        return model->averageModel->topDangerousCells();
    }

    void close()
    {
        coordinator->stop();
    }

private:
    std::string configFilePath;
    double samplePeriod;
    int cellsPerDecision;
    std::shared_ptr<WildfireHybridCoupled> model;
    std::unique_ptr<cadmium::RootCoordinator> coordinator;
};
