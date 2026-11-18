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

enum class AircraftPhase
{
    Idle,
    FlyingToTarget,
    Dropping,
    Returning
};

struct AircraftState
{
    double x;
    double y;
    double waterLeft;
    AircraftPhase phase;
    double sigma;

    explicit AircraftState(double baseX, double baseY, double tankSize)
        : x(baseX), y(baseY), waterLeft(tankSize), phase(AircraftPhase::Idle), sigma(std::numeric_limits<double>::infinity()) {}
};

inline std::ostream& operator<<(std::ostream& os, const AircraftState& s)
{
    return os << s.x << "," << s.y << "," << s.waterLeft << "," << static_cast<int>(s.phase) << "," << s.sigma;
}
