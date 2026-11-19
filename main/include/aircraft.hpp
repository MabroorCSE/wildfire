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
    Returning,
    Refilling
};

struct AircraftState
{
    double x;
    double y;
    double targetX;
    double targetY;
    double waterLeft;
    AircraftPhase phase;
    double sigma;

    explicit AircraftState(double baseX, double baseY, double tankSize)
        : x(baseX), y(baseY), targetX(baseX), targetY(baseY), waterLeft(tankSize), phase(AircraftPhase::Idle), sigma(std::numeric_limits<double>::infinity()) {}
};

inline std::ostream& operator<<(std::ostream& os, const AircraftState& s)
{
    return os << s.x << "," << s.y << "," << s.targetX << "," << s.targetY << "," << s.waterLeft << "," << static_cast<int>(s.phase) << "," << s.sigma;
}

//ids come from config, '_' is assumed present
inline std::pair<double, double> parseCellId(const std::string& id)
{
    size_t i = id.find('_');
    double x = std::stod(id.substr(0, i));
    double y = std::stod(id.substr(i+1));
    return {x, y};
}
