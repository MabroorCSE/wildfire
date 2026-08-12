#pragma once

#include <algorithm>
#include <iostream>
#include <limits>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <cadmium/core/modeling/atomic.hpp>
#include <cadmium/celldevs/core/msg.hpp>
#include "cell_command.hpp"
#include "state.hpp"

struct AverageState
{
    std::unordered_map<std::string, State> lastStateByCell;
    std::unordered_set<std::string> ignitedAsOfLastSample;

    double timeToNextSample;
    double percentCellsIgnited;
    double reward;

    explicit AverageState(double samplePeriod)
        : lastStateByCell(), ignitedAsOfLastSample(), timeToNextSample(samplePeriod),
          percentCellsIgnited(0.0), reward(0.0) {}
};

inline std::ostream& operator<<(std::ostream& os, const AverageState& s)
{
    return os << s.percentCellsIgnited << "," << s.reward;
}

inline std::unordered_set<std::string> ignitedCellSet(const std::unordered_map<std::string, State>& lastStateByCell)
{
    std::unordered_set<std::string> ignited;
    for (const auto& [cellId, state] : lastStateByCell)
    {
        if (state.ignited)
        {
            ignited.insert(cellId);
        }
    }
    return ignited;
}

inline double computePercentIgnited(const std::unordered_map<std::string, State>& lastStateByCell, size_t ignitedCount)
{
    return lastStateByCell.empty() ? 0.0 : 100.0 * static_cast<double>(ignitedCount) / static_cast<double>(lastStateByCell.size());
}

//Counts cells ignited now but not at the last sample; re-ignitions after a suppression count too.
inline size_t countNewlyIgnited(const std::unordered_set<std::string>& ignitedNow, const std::unordered_set<std::string>& ignitedBefore)
{
    size_t count = 0;
    for (const auto& cellId : ignitedNow)
    {
        if (!ignitedBefore.count(cellId))
        {
            count++;
        }
    }
    return count;
}

//RL-environment side of the hybrid model. Tracks the full state of every cell, and recomputes
//its summary (percent on fire, reward, resources) once per samplePeriod. requestAction() lets an
//outside driver (see rl_environment.hpp) target any cell for extinguishing on the next sample.
class AverageAtomic : public cadmium::Atomic<AverageState>
{
public:
    cadmium::BigPort<cadmium::celldevs::CellStateMessage<std::string, State>> cellStateIn;
    cadmium::Port<double> percentIgnitedOut;
    cadmium::Port<double> rewardOut;
    cadmium::Port<CellCommand> cellCommandOut;
    double samplePeriod;
    int cellsPerDecision;  // how many cells topDangerousCells() picks; change freely

    explicit AverageAtomic(const std::string& id, double samplePeriod = 3600.0, int cellsPerDecision = 1)
        : cadmium::Atomic<AverageState>(id, AverageState(samplePeriod)),
          samplePeriod(samplePeriod), cellsPerDecision(cellsPerDecision)
    {
        cellStateIn = addInBigPort<cadmium::celldevs::CellStateMessage<std::string, State>>("cellStateIn");
        percentIgnitedOut = addOutPort<double>("percentIgnitedOut");
        rewardOut = addOutPort<double>("rewardOut");
        cellCommandOut = addOutPort<CellCommand>("cellCommandOut");
    }

    void requestActions(const std::vector<std::string>& targetCellIds) const
    {
        pendingActions = targetCellIds;
    }

    [[nodiscard]] double lastPercentIgnited() const { return state.percentCellsIgnited; }
    [[nodiscard]] double lastReward() const { return state.reward; }

    [[nodiscard]] std::vector<std::string> ignitedCellIds() const
    {
        auto ignited = ignitedCellSet(state.lastStateByCell);
        return {ignited.begin(), ignited.end()};
    }

    //Ranks currently-burning cells by rateOfSpread (fastest first) using everything this model
    //already knows about them, and returns the top cellsPerDecision ids -- the cells most worth
    //targeting right now.
    [[nodiscard]] std::vector<std::string> topDangerousCells() const
    {
        std::vector<std::pair<std::string, double>> burning;
        for (const auto& [cellId, cellState] : state.lastStateByCell)
        {
            if (cellState.ignited)
            {
                burning.emplace_back(cellId, cellState.rateOfSpread);
            }
        }
        std::sort(burning.begin(), burning.end(), [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
        if (burning.size() > static_cast<size_t>(cellsPerDecision))
        {
            burning.resize(cellsPerDecision);
        }
        std::vector<std::string> result;
        result.reserve(burning.size());
        for (const auto& [cellId, rate] : burning)
        {
            result.push_back(cellId);
        }
        return result;
    }

    void internalTransition(AverageState& s) const override
    {
        auto ignitedNow = ignitedCellSet(s.lastStateByCell);
        s.reward = -static_cast<double>(countNewlyIgnited(ignitedNow, s.ignitedAsOfLastSample));
        s.percentCellsIgnited = computePercentIgnited(s.lastStateByCell, ignitedNow.size());
        s.ignitedAsOfLastSample = std::move(ignitedNow);
        s.timeToNextSample = samplePeriod;
        pendingActions.clear();
    }

    void externalTransition(AverageState& s, double e) const override
    {
        s.timeToNextSample -= e;
        for (const auto& msg : cellStateIn->getBag())
        {
            s.lastStateByCell[msg->cellId] = *msg->state;
        }
    }

    void output(const AverageState& s) const override
    {
        auto ignitedNow = ignitedCellSet(s.lastStateByCell);
        percentIgnitedOut->addMessage(computePercentIgnited(s.lastStateByCell, ignitedNow.size()));
        rewardOut->addMessage(-static_cast<double>(countNewlyIgnited(ignitedNow, s.ignitedAsOfLastSample)));
        for (const auto& targetCellId : pendingActions)
        {
            cellCommandOut->addMessage(CellCommand{targetCellId});
        }
    }

    [[nodiscard]] double timeAdvance(const AverageState& s) const override
    {
        return s.timeToNextSample;
    }

private:
    mutable std::vector<std::string> pendingActions;
};
