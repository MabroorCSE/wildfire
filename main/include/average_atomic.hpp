#pragma once

#include <iostream>
#include <limits>
#include <string>
#include <unordered_map>
#include <cadmium/core/modeling/atomic.hpp>
#include <cadmium/celldevs/core/msg.hpp>
#include "state.hpp"

//State of the atomic model: last known ignition status per cell, the last computed percentage
//(kept only so it can be logged), and a countdown to the next periodic sample.
struct AverageState
{
    std::unordered_map<std::string, bool> lastIgnitedByCell;
    double percentCellsIgnited;
    double timeToNextSample;

    explicit AverageState(double samplePeriod)
        : lastIgnitedByCell(), percentCellsIgnited(0.0), timeToNextSample(samplePeriod) {}
};

inline std::ostream& operator<<(std::ostream& os, const AverageState& s)
{
    return os << s.percentCellsIgnited;
}

//Computes the percentage of cells currently on fire from the last known ignition status of every cell.
inline double computePercentIgnited(const std::unordered_map<std::string, bool>& lastIgnitedByCell)
{
    if (lastIgnitedByCell.empty())
    {
        return 0.0;
    }
    size_t ignitedCount = 0;
    for (const auto& [cellId, ignited] : lastIgnitedByCell)
    {
        if (ignited)
        {
            ignitedCount++;
        }
    }
    return 100.0 * static_cast<double>(ignitedCount) / static_cast<double>(lastIgnitedByCell.size());
}

//Atomic DEVS model connected to every cell of the wildfire grid. It keeps track of the ignition
//status reported by each cell, but only recomputes and outputs the percentage of cells on fire
//once per samplePeriod, regardless of how many cell updates arrive in between.
class AverageAtomic : public cadmium::Atomic<AverageState>
{
public:
    cadmium::BigPort<cadmium::celldevs::CellStateMessage<std::string, State>> cellStateIn;
    cadmium::Port<double> percentIgnitedOut;
    double samplePeriod; //simulation time (seconds) between two samples

    explicit AverageAtomic(const std::string& id, double samplePeriod = 3600.0)
        : cadmium::Atomic<AverageState>(id, AverageState(samplePeriod)), samplePeriod(samplePeriod)
    {
        cellStateIn = addInBigPort<cadmium::celldevs::CellStateMessage<std::string, State>>("cellStateIn");
        percentIgnitedOut = addOutPort<double>("percentIgnitedOut");
    }

    //Fires once every samplePeriod: the percentage was just emitted through output(), so it is
    //stored here (for logging) and the countdown restarts.
    void internalTransition(AverageState& s) const override
    {
        s.percentCellsIgnited = computePercentIgnited(s.lastIgnitedByCell);
        s.timeToNextSample = samplePeriod;
    }

    //Cell updates only update the tracked ignition data; they never trigger a recompute/output by themselves.
    void externalTransition(AverageState& s, double e) const override
    {
        s.timeToNextSample -= e;
        for (const auto& msg : cellStateIn->getBag())
        {
            s.lastIgnitedByCell[msg->cellId] = msg->state->ignited;
        }
    }

    //Called right before the periodic internal transition: emits the percentage based on the
    //latest ignition data collected since the last sample.
    void output(const AverageState& s) const override
    {
        percentIgnitedOut->addMessage(computePercentIgnited(s.lastIgnitedByCell));
    }

    [[nodiscard]] double timeAdvance(const AverageState& s) const override
    {
        return s.timeToNextSample;
    }
};
